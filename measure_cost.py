#!/usr/bin/env python3
"""
Measure what one FitFindr run costs. ← CAPSTONE, MILESTONE 3

    python measure_cost.py              10 full runs, cache off
    python measure_cost.py --runs 20

Runs the agent end to end on matching queries (so both model calls happen),
with the response cache OFF, then reads back the run-log records those runs
wrote and averages them. Nothing here is estimated: tokens come from the
service's own usage_metadata, time from the wall clock.

Dollars are tokens x the published per-token rate for config.MODEL. The
tokens are the measurement; the rate is the only number taken from a page.
"""

import argparse
import os

os.environ["AI201_CACHE"] = "0"  # before config is imported: real calls only

import config  # noqa: E402
import runlog  # noqa: E402
from agent import run_agent  # noqa: E402
from utils.data_loader import get_example_wardrobe  # noqa: E402

# Standard (paid) tier, gemini-3.5-flash-lite, USD per 1M tokens.
# https://ai.google.dev/gemini-api/docs/pricing — checked 2026-11-14.
PRICE_IN_PER_M = 0.30
PRICE_OUT_PER_M = 2.50

QUERIES = [
    "vintage graphic tee under $30",
    "90s track jacket in size M",
    "silk slip dress in midi length under $40",
    "platform sneakers size 8",
    "denim jacket under $50",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=10)
    args = parser.parse_args()

    seen = {r.get("run_id") for r in runlog.read()}
    for i in range(args.runs):
        query = QUERIES[i % len(QUERIES)]
        session = run_agent(query, get_example_wardrobe())
        status = session["error_type"] or ("fallback" if session["fallbacks"] else "ok")
        print(f"  run {i + 1:>2}/{args.runs}  {status:<10} {query}")

    records = [r for r in runlog.read() if r.get("run_id") not in seen]
    full = [r for r in records if r["outcome"] in ("ok", "ok_fallback")]
    if not full:
        print("No complete runs to measure.")
        return

    n = len(full)
    avg = lambda key: sum(r[key] for r in full) / n  # noqa: E731
    p_in, p_out = avg("prompt_tokens"), avg("output_tokens")
    dollars = p_in / 1e6 * PRICE_IN_PER_M + p_out / 1e6 * PRICE_OUT_PER_M
    work_s = sum(r["duration_ms"] - r["wait_ms"] for r in full) / n / 1000

    print(f"\n{n} complete runs of {len(records)} measured ({config.MODEL}, cache off)")
    print(f"  model calls / run     {avg('model_calls'):.2f}")
    print(f"  prompt tokens / run   {p_in:.1f}")
    print(f"  output tokens / run   {p_out:.1f}")
    print(f"  wall time / run       {avg('duration_ms') / 1000:.2f}s "
          f"(of which rate-limit waiting {avg('wait_ms') / 1000:.2f}s)")
    print(f"  working time / run    {work_s:.2f}s")
    print(f"  $ / run (paid tier)   ${dollars:.6f}")


if __name__ == "__main__":
    main()
