"""Core event types for the backtester event loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class EventType(str, Enum):
    MARKET = "MARKET"
    SIGNAL = "SIGNAL"
    ORDER = "ORDER"
    FILL = "FILL"


class Direction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class Event:
    """Base event; subclasses carry domain payload."""

    type: EventType


@dataclass(frozen=True)
class MarketEvent(Event):
    """New bar / tick available for a symbol."""

    type: EventType = field(default=EventType.MARKET, init=False)
    symbol: str = ""
    timestamp: Optional[datetime] = None
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0


@dataclass(frozen=True)
class SignalEvent(Event):
    """Strategy intent to enter/exit."""

    type: EventType = field(default=EventType.SIGNAL, init=False)
    symbol: str = ""
    timestamp: Optional[datetime] = None
    direction: Direction = Direction.BUY
    strength: float = 1.0  # 0..1 sizing hint


@dataclass(frozen=True)
class OrderEvent(Event):
    """Portfolio-issued order to the execution handler."""

    type: EventType = field(default=EventType.ORDER, init=False)
    symbol: str = ""
    timestamp: Optional[datetime] = None
    direction: Direction = Direction.BUY
    quantity: float = 0.0
    order_type: str = "MKT"


@dataclass(frozen=True)
class FillEvent(Event):
    """Simulated fill from the execution handler."""

    type: EventType = field(default=EventType.FILL, init=False)
    symbol: str = ""
    timestamp: Optional[datetime] = None
    direction: Direction = Direction.BUY
    quantity: float = 0.0
    fill_price: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0

    @property
    def signed_quantity(self) -> float:
        return self.quantity if self.direction == Direction.BUY else -self.quantity

    @property
    def total_cost(self) -> float:
        """Cash impact of fill including commission (buy positive outflow)."""
        notional = self.fill_price * self.quantity
        if self.direction == Direction.BUY:
            return notional + self.commission
        return -(notional - self.commission)
