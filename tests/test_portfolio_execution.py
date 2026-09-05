from backtester.event_queue import EventQueue
from backtester.events import Direction, MarketEvent, OrderEvent
from backtester.execution import CostModel, ExecutionHandler
from backtester.portfolio import Portfolio


def test_fill_updates_cash_and_position():
    q = EventQueue()
    port = Portfolio(events=q, initial_cash=10_000.0)
    ex = ExecutionHandler(
        events=q,
        cost_model=CostModel(commission_per_share=0.01, commission_min=1.0, slippage_bps=10.0),
    )
    market = MarketEvent(symbol="SYN", close=100.0)
    ex.on_market(market)
    port.on_market(market)
    q.put(OrderEvent(symbol="SYN", direction=Direction.BUY, quantity=10))
    order = q.get()
    ex.execute_order(order)
    fill = q.get()
    assert fill is not None
    port.on_fill(fill)
    assert port.positions["SYN"].quantity == 10
    # price slipped up by 10 bps => 100.1; commission max(1, 0.1)=1
    assert fill.fill_price == 100.1
    assert abs(port.cash - (10_000 - 100.1 * 10 - 1.0)) < 1e-9


def test_costs_reduce_equity_vs_zero_cost():
    def run(costs: CostModel) -> float:
        q = EventQueue()
        port = Portfolio(events=q, initial_cash=10_000.0)
        ex = ExecutionHandler(events=q, cost_model=costs)
        m = MarketEvent(symbol="SYN", close=50.0)
        ex.on_market(m)
        port.on_market(m)
        q.put(OrderEvent(symbol="SYN", direction=Direction.BUY, quantity=20))
        ex.execute_order(q.get())
        port.on_fill(q.get())
        # mark at same price
        port.on_market(MarketEvent(symbol="SYN", close=50.0))
        return port.total_equity()

    zero = CostModel(0.0, 0.0, 0.0)
    costly = CostModel(0.01, 1.0, 10.0)
    assert run(costly) < run(zero)
