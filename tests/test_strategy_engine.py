from backtester.data import make_synthetic_bars
from backtester.engine import BacktestEngine, run_slice
from backtester.execution import CostModel
from backtester.performance import compute_metrics


def test_sma_engine_produces_fills_and_metrics():
    bars = make_synthetic_bars(n=120, seed=7, symbol="SYN")
    engine = BacktestEngine(
        bars=bars,
        symbol="SYN",
        cost_model=CostModel(0.005, 1.0, 5.0),
        fast=5,
        slow=15,
    )
    metrics = engine.run()
    assert metrics["trade_count"] >= 1
    assert metrics["n_bars"] >= 1
    assert "total_return" in metrics
    assert "sharpe" in metrics
    assert "max_drawdown" in metrics
    assert metrics["max_drawdown"] <= 0.0


def test_metrics_reproducible_on_synthetic_bars():
    a = run_slice(n=200, seed=42, with_costs=True)
    b = run_slice(n=200, seed=42, with_costs=True)
    assert a == b
    assert a["trade_count"] == b["trade_count"]


def test_explicit_costs_cut_equity_vs_zero_cost():
    with_c = run_slice(n=200, seed=42, with_costs=True)
    zero = run_slice(n=200, seed=42, with_costs=False)
    assert with_c["final_equity"] < zero["final_equity"]
    assert with_c["trade_count"] == zero["trade_count"]


def test_compute_metrics_empty():
    import pandas as pd

    m = compute_metrics(pd.Series(dtype=float), trade_count=0)
    assert m["total_return"] == 0.0
    assert m["trade_count"] == 0
