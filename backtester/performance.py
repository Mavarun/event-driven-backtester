"""Reproducible performance attribution on equity curves."""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd


def compute_metrics(
    equity: pd.Series,
    trade_count: int = 0,
    periods_per_year: float = 252.0,
) -> Dict[str, Any]:
    """Returns, Sharpe, max drawdown, and trade count from an equity series."""
    if equity is None or len(equity) < 2:
        return {
            "total_return": 0.0,
            "sharpe": 0.0,
            "max_drawdown": 0.0,
            "trade_count": int(trade_count),
            "final_equity": float(equity.iloc[-1]) if equity is not None and len(equity) else 0.0,
            "n_bars": 0 if equity is None else int(len(equity)),
        }

    eq = equity.astype(float).dropna()
    rets = eq.pct_change().dropna()
    total_return = float(eq.iloc[-1] / eq.iloc[0] - 1.0)
    vol = float(rets.std(ddof=0))
    mean = float(rets.mean())
    sharpe = 0.0 if vol == 0.0 else float((mean / vol) * np.sqrt(periods_per_year))
    peak = eq.cummax()
    dd = (eq / peak) - 1.0
    max_dd = float(dd.min()) if len(dd) else 0.0
    return {
        "total_return": total_return,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "trade_count": int(trade_count),
        "final_equity": float(eq.iloc[-1]),
        "n_bars": int(len(eq)),
    }
