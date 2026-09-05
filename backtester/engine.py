"""Event-loop engine wiring data -> strategy -> portfolio -> execution."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

import pandas as pd

from backtester.data import bars_to_market_events, make_synthetic_bars
from backtester.event_queue import EventQueue
from backtester.events import EventType, FillEvent, MarketEvent, OrderEvent, SignalEvent
from backtester.execution import CostModel, ExecutionHandler
from backtester.performance import compute_metrics
from backtester.portfolio import Portfolio
from backtester.strategy import SMACrossoverStrategy


class BacktestEngine:
    """Drain the event queue until empty after each market bar."""

    def __init__(
        self,
        bars: pd.DataFrame,
        symbol: str = "SYN",
        initial_cash: float = 100_000.0,
        cost_model: Optional[CostModel] = None,
        fast: int = 10,
        slow: int = 30,
    ) -> None:
        self.bars = bars
        self.symbol = symbol
        self.events = EventQueue()
        self.portfolio = Portfolio(events=self.events, initial_cash=initial_cash)
        self.execution = ExecutionHandler(events=self.events, cost_model=cost_model)
        self.strategy = SMACrossoverStrategy(
            events=self.events, symbol=symbol, fast=fast, slow=slow
        )

    def run(self) -> Dict[str, Any]:
        for market in bars_to_market_events(self.bars, symbol=self.symbol):
            self.events.put(market)
            self._drain()
        equity = self.portfolio.equity_series()
        metrics = compute_metrics(equity, trade_count=self.portfolio.trade_count)
        metrics["initial_cash"] = self.portfolio.initial_cash
        metrics["final_cash"] = self.portfolio.cash
        return metrics

    def _drain(self) -> None:
        while not self.events.empty():
            event = self.events.get()
            if event is None:
                break
            if event.type == EventType.MARKET:
                assert isinstance(event, MarketEvent)
                self.execution.on_market(event)
                self.strategy.on_market(event)
                self.portfolio.on_market(event)
            elif event.type == EventType.SIGNAL:
                assert isinstance(event, SignalEvent)
                self.portfolio.on_signal(event)
            elif event.type == EventType.ORDER:
                assert isinstance(event, OrderEvent)
                self.execution.execute_order(event)
            elif event.type == EventType.FILL:
                assert isinstance(event, FillEvent)
                self.portfolio.on_fill(event)


def run_slice(
    n: int = 252,
    seed: int = 42,
    with_costs: bool = True,
    initial_cash: float = 100_000.0,
) -> Dict[str, Any]:
    """Convenience runner for the event-loop fills hypothesis slice."""
    bars = make_synthetic_bars(n=n, seed=seed, symbol="SYN")
    costs = (
        CostModel(commission_per_share=0.005, commission_min=1.0, slippage_bps=5.0)
        if with_costs
        else CostModel(commission_per_share=0.0, commission_min=0.0, slippage_bps=0.0)
    )
    engine = BacktestEngine(
        bars=bars, symbol="SYN", initial_cash=initial_cash, cost_model=costs
    )
    metrics = engine.run()
    metrics["with_costs"] = with_costs
    metrics["seed"] = seed
    return metrics
