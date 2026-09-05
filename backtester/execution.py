"""Simulated execution with explicit commission and slippage costs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from backtester.event_queue import EventQueue
from backtester.events import Direction, FillEvent, MarketEvent, OrderEvent


@dataclass
class CostModel:
    """Explicit transaction costs applied on every fill."""

    commission_per_share: float = 0.005
    commission_min: float = 1.0
    slippage_bps: float = 5.0  # basis points of notional price impact

    def commission(self, quantity: float) -> float:
        return max(self.commission_min, abs(quantity) * self.commission_per_share)

    def slip_price(self, price: float, direction: Direction) -> tuple[float, float]:
        slip = price * (self.slippage_bps / 10_000.0)
        if direction == Direction.BUY:
            return price + slip, slip
        return price - slip, slip


class ExecutionHandler:
    """Immediate market fills at last close +/- slippage + commission."""

    def __init__(
        self,
        events: EventQueue,
        cost_model: Optional[CostModel] = None,
    ) -> None:
        self.events = events
        self.costs = cost_model or CostModel()
        self._last_price: Dict[str, float] = {}
        self._last_ts: Dict[str, object] = {}

    def on_market(self, event: MarketEvent) -> None:
        self._last_price[event.symbol] = event.close
        self._last_ts[event.symbol] = event.timestamp

    def execute_order(self, order: OrderEvent) -> None:
        price = self._last_price.get(order.symbol)
        if price is None or order.quantity <= 0:
            return
        fill_price, slip = self.costs.slip_price(price, order.direction)
        commission = self.costs.commission(order.quantity)
        fill = FillEvent(
            symbol=order.symbol,
            timestamp=order.timestamp or self._last_ts.get(order.symbol),
            direction=order.direction,
            quantity=order.quantity,
            fill_price=fill_price,
            commission=commission,
            slippage=slip,
        )
        self.events.put(fill)
