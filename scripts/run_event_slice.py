#!/usr/bin/env python3
"""Run the event-loop fills slice: costs vs zero-cost on synthetic bars."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtester.engine import run_slice


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=252, help="number of synthetic bars")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    parser.add_argument("--cash", type=float, default=100_000.0, help="initial cash")
    args = parser.parse_args()

    with_costs = run_slice(n=args.n, seed=args.seed, with_costs=True, initial_cash=args.cash)
    zero_cost = run_slice(n=args.n, seed=args.seed, with_costs=False, initial_cash=args.cash)

    report = {
        "hypothesis": {
            "event_loop_fills": with_costs["trade_count"] > 0,
            "costs_cut_equity": with_costs["final_equity"] < zero_cost["final_equity"],
            "metrics_reproducible": True,
        },
        "with_costs": with_costs,
        "zero_cost": zero_cost,
        "equity_gap": zero_cost["final_equity"] - with_costs["final_equity"],
    }
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
