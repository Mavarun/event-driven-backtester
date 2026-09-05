"""Cash, positions, and order generation from signals."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd

from backtester.event_queue import EventQueue
from backtester.events import (
    Direction,
    FillEvent,
    MarketEvent,
    OrderEvent,
    SignalEvent,
)


@dataclass
class Position:
    quantity: float = 0.0
    avg_price: float = 0.0


@dataclass
class Portfolio:
    """Tracks cash/positions; emits OrderEvents; records equity curve."""

    events: EventQueue
    initial_cash: float = 100_000.0
    cash: float = field(init=False)
    positions: Dict[str, Position] = field(default_factory=dict)
    _last_price: Dict[str, float] = field(default_factory=dict)
    equity_curve: List[dict] = field(default_factory=list)
    fills: List[FillEvent] = field(default_factory=list)
    trade_count: int = 0

    def __post_init__(self) -> None:
        self.cash = self.initial_cash

    def on_market(self, event: MarketEvent) -> None:
        self._last_price[event.symbol] = event.close
        self._mark_equity(event.timestamp)

    def on_signal(self, signal: SignalEvent) -> None:
        price = self._last_price.get(signal.symbol)
        if price is None or price <= 0:
            return
        pos = self.positions.get(signal.symbol, Position())
        target_frac = max(0.0, min(1.0, signal.strength))
        equity = self.total_equity()
        if signal.direction == Direction.BUY:
            target_qty = (equity * target_frac) / price
            delta = target_qty - pos.quantity
            if delta > 1e-8:
                self.events.put(
                    OrderEvent(
                        symbol=signal.symbol,
                        timestamp=signal.timestamp,
                        direction=Direction.BUY,
                        quantity=delta,
                    )
                )
        else:  # SELL / flatten or short-not-supported: reduce long
            if pos.quantity > 1e-8:
                qty = pos.quantity * target_frac if target_frac < 1.0 else pos.quantity
                qty = min(qty, pos.quantity)
                if qty > 1e-8:
                    self.events.put(
                        OrderEvent(
                            symbol=signal.symbol,
                            timestamp=signal.timestamp,
                            direction=Direction.SELL,
                            quantity=qty,
                        )
                    )

    def on_fill(self, fill: FillEvent) -> None:
        pos = self.positions.setdefault(fill.symbol, Position())
        self.fills.append(fill)
        self.trade_count += 1
        if fill.direction == Direction.BUY:
            new_qty = pos.quantity + fill.quantity
            if new_qty > 0:
                pos.avg_price = (
                    (pos.avg_price * pos.quantity) + (fill.fill_price * fill.quantity)
                ) / new_qty
            pos.quantity = new_qty
            self.cash -= fill.fill_price * fill.quantity + fill.commission
        else:
            pos.quantity -= fill.quantity
            self.cash += fill.fill_price * fill.quantity - fill.commission
            if abs(pos.quantity) < 1e-10:
                pos.quantity = 0.0
                pos.avg_price = 0.0
        self._last_price[fill.symbol] = fill.fill_price
        self._mark_equity(fill.timestamp)

    def market_value(self) -> float:
        total = 0.0
        for sym, pos in self.positions.items():
            px = self._last_price.get(sym, pos.avg_price)
            total += pos.quantity * px
        return total

    def total_equity(self) -> float:
        return self.cash + self.market_value()

    def _mark_equity(self, timestamp) -> None:
        self.equity_curve.append(
            {
                "timestamp": timestamp,
                "cash": self.cash,
                "market_value": self.market_value(),
                "equity": self.total_equity(),
            }
        )

    def equity_series(self) -> pd.Series:
        if not self.equity_curve:
            return pd.Series(dtype=float)
        df = pd.DataFrame(self.equity_curve)
        return pd.Series(df["equity"].values, index=pd.Index(df["timestamp"]), name="equity")
