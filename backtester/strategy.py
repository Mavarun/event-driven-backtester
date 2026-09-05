"""Simple SMA crossover strategy emitting SignalEvents."""

from __future__ import annotations

from collections import deque
from typing import Deque, Optional

from backtester.event_queue import EventQueue
from backtester.events import Direction, MarketEvent, SignalEvent


class SMACrossoverStrategy:
    """Long when fast SMA crosses above slow SMA; flatten on cross below."""

    def __init__(
        self,
        events: EventQueue,
        symbol: str,
        fast: int = 10,
        slow: int = 30,
    ) -> None:
        if fast >= slow:
            raise ValueError("fast window must be < slow window")
        self.events = events
        self.symbol = symbol
        self.fast = fast
        self.slow = slow
        self._closes: Deque[float] = deque(maxlen=slow)
        self._position: int = 0  # 0 flat, 1 long

    def on_market(self, event: MarketEvent) -> None:
        if event.symbol != self.symbol:
            return
        self._closes.append(event.close)
        if len(self._closes) < self.slow:
            return
        closes = list(self._closes)
        fast_sma = sum(closes[-self.fast :]) / self.fast
        slow_sma = sum(closes) / self.slow
        if fast_sma > slow_sma and self._position <= 0:
            self._position = 1
            self.events.put(
                SignalEvent(
                    symbol=self.symbol,
                    timestamp=event.timestamp,
                    direction=Direction.BUY,
                    strength=1.0,
                )
            )
        elif fast_sma < slow_sma and self._position >= 1:
            self._position = 0
            self.events.put(
                SignalEvent(
                    symbol=self.symbol,
                    timestamp=event.timestamp,
                    direction=Direction.SELL,
                    strength=1.0,
                )
            )
