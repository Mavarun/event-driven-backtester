# event-driven-backtester

Event-driven backtester slice: **event loop → signals → orders → fills → positions → performance attribution**.

Not live PnL. Stack: **pandas**, **numpy**.

## Hypotheses (this slice)

1. An event loop with `MarketEvent` / `SignalEvent` / `OrderEvent` / `FillEvent` can simulate fills and positions.
2. Explicit costs (commission + slippage) reduce equity versus a zero-cost baseline.
3. Performance attribution (returns, Sharpe, max drawdown, trade count) is reproducible on synthetic bars.

## Layout

```
backtester/
  events.py          # Market/Signal/Order/Fill events
  event_queue.py     # FIFO queue
  portfolio.py       # cash, positions, order sizing
  execution.py       # fills with CostModel
  strategy.py        # SMA crossover
  data.py            # synthetic OHLCV bars
  engine.py          # event-loop wiring
  performance.py     # returns, Sharpe, max DD, trade count
scripts/run_event_slice.py
tests/
```

## Quick start

```bash
pip install -r requirements.txt
pytest -q
python scripts/run_event_slice.py --n 252 --seed 42
```

## Event loop

For each bar the engine enqueues a `MarketEvent`, then drains the queue:

1. **MARKET** → execution price book, strategy, portfolio mark-to-market  
2. **SIGNAL** → portfolio emits `OrderEvent`  
3. **ORDER** → execution handler emits `FillEvent` (slippage + commission)  
4. **FILL** → portfolio updates cash/position  

## Costs

`CostModel(commission_per_share, commission_min, slippage_bps)` is applied on every fill. The slice script compares `with_costs` vs `zero_cost` and reports the equity gap.

## Metrics

`compute_metrics(equity_series, trade_count)` returns `total_return`, `sharpe`, `max_drawdown`, `trade_count`, `final_equity`, `n_bars`. Same seed ⇒ identical metrics.
