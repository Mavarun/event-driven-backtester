"""Synthetic OHLCV bar generators for reproducible slices."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def make_synthetic_bars(
    n: int = 252,
    start_price: float = 100.0,
    drift: float = 0.0003,
    vol: float = 0.012,
    seed: int = 42,
    symbol: str = "SYN",
    start: str = "2020-01-01",
) -> pd.DataFrame:
    """Generate deterministic geometric-brownian-like daily bars."""
    rng = np.random.default_rng(seed)
    rets = drift + vol * rng.standard_normal(n)
    close = start_price * np.cumprod(1.0 + rets)
    open_ = np.concatenate([[start_price], close[:-1]])
    high = np.maximum(open_, close) * (1.0 + 0.002 * rng.random(n))
    low = np.minimum(open_, close) * (1.0 - 0.002 * rng.random(n))
    volume = rng.integers(100_000, 500_000, size=n).astype(float)
    idx = pd.bdate_range(start=start, periods=n)
    df = pd.DataFrame(
        {
            "symbol": symbol,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=idx,
    )
    df.index.name = "timestamp"
    return df


def bars_to_market_events(df: pd.DataFrame, symbol: Optional[str] = None):
    """Yield MarketEvent objects in chronological order."""
    from backtester.events import MarketEvent

    sym = symbol or (str(df["symbol"].iloc[0]) if "symbol" in df.columns else "SYN")
    for ts, row in df.iterrows():
        yield MarketEvent(
            symbol=sym,
            timestamp=ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts,
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row["volume"]),
        )
