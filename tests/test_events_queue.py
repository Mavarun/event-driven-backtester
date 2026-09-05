from backtester.event_queue import EventQueue
from backtester.events import Direction, EventType, FillEvent, MarketEvent, OrderEvent, SignalEvent


def test_event_types_and_fifo_queue():
    q = EventQueue()
    m = MarketEvent(symbol="SYN", close=100.0)
    s = SignalEvent(symbol="SYN", direction=Direction.BUY)
    o = OrderEvent(symbol="SYN", direction=Direction.BUY, quantity=10)
    f = FillEvent(
        symbol="SYN",
        direction=Direction.BUY,
        quantity=10,
        fill_price=100.1,
        commission=1.0,
        slippage=0.1,
    )
    assert m.type == EventType.MARKET
    assert s.type == EventType.SIGNAL
    assert o.type == EventType.ORDER
    assert f.type == EventType.FILL
    assert f.signed_quantity == 10
    assert f.total_cost == 100.1 * 10 + 1.0

    for ev in (m, s, o, f):
        q.put(ev)
    assert len(q) == 4
    assert q.get() is m
    assert q.get() is s
    assert q.get() is o
    assert q.get() is f
    assert q.empty()
