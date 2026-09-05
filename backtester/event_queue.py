"""FIFO event queue driving the backtester loop."""

from __future__ import annotations

from collections import deque
from typing import Deque, Iterator, Optional

from backtester.events import Event


class EventQueue:
    """Simple FIFO queue; put/get used by engine and components."""

    def __init__(self) -> None:
        self._q: Deque[Event] = deque()

    def put(self, event: Event) -> None:
        self._q.append(event)

    def get(self) -> Optional[Event]:
        if not self._q:
            return None
        return self._q.popleft()

    def empty(self) -> bool:
        return not self._q

    def __len__(self) -> int:
        return len(self._q)

    def __iter__(self) -> Iterator[Event]:
        while not self.empty():
            ev = self.get()
            if ev is not None:
                yield ev
