#!/usr/bin/env python3
"""
The capstone test. ← CAPSTONE, MILESTONE 5

    python capstone_trials.py --label before --trial 1

One trial = 5 attempts against each of the 5 criteria in criteria.md
("Capstone criteria"). Run it three times per label. Cache is off; every
attempt is a real run. Each trial writes:

    logs/capstone_<label>.jsonl                 the run-log records it produced
    results/capstone_<label>_trial<N>.json      per-attempt pass/fail + evidence

How each attempt is scored — decided before running, applied by code:

  C1 timeout     `python app.py ask <query>` as its own process with
                 AI201_MODEL_TIMEOUT=0.01. PASS = exit code 0, no traceback,
                 the user sees the timeout message, and the run log gained a
                 record with outcome=error, error_type=ModelTimeout.
  C2 empty       run_agent with AI201_FAULT=empty. PASS = record has
                 outcome=ok_fallback with create_fit_card in `fallbacks`, and
                 the fit card is non-empty and names the item's title and its
                 price as "$NN.NN" ("usable caption").
  C3 malformed   serve.py running; POST /ask with 5 different bad bodies.
                 PASS = HTTP 400, a log record with outcome=rejected and
                 model_calls=0, and no agent-run record appeared.
  C4 waiting     normal runs back to back in one process until 5 of them hit
                 the rate limiter. time.sleep inside generate.py is wrapped to
                 measure, independently, how long each run actually slept.
                 PASS = wait_ms > 0 and within 100 ms of the measured sleep.
  C5 two calls   run_agent on a normal matching query. PASS = outcome=ok and
                 model_calls == 2.
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
QUERIES = [
    "vintage graphic tee under $30",
    "90s track jacket in size M",
    "silk slip dress in midi length under $40",
    "platform sneakers size 8",
    "denim jacket under $50",
]
BAD_BODIES = ["{}", '{"query": 123}', "[1, 2]", "not json", '{"query": "   "}']
PYTHON = sys.executable


def new_records(log: Path, before: int) -> list[dict]:
    lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    return [json.loads(l) for l in lines[before:] if l.strip()]


def line_count(log: Path) -> int:
    return len(log.read_text(encoding="utf-8").splitlines()) if log.exists() else 0


# ── C1 ──────────────────────────────────────────────────────────────────────

def c1_timeout(log: Path) -> list[dict]:
    out = []
    for q in QUERIES:
        n0 = line_count(log)
        env = {**os.environ, "AI201_MODEL_TIMEOUT": "0.01"}
        t0 = time.perf_counter()
        proc = subprocess.run([PYTHON, "app.py", "ask", q], cwd=ROOT, env=env,
                              capture_output=True, text=True, timeout=120)
        elapsed = round(time.perf_counter() - t0, 2)
        recs = new_records(log, n0)
        rec = recs[-1] if recs else {}
        text = proc.stdout + proc.stderr
        ok = (proc.returncode == 0 and "Traceback" not in text
              and "didn't answer within" in text
              and rec.get("outcome") == "error" and rec.get("error_type") == "ModelTimeout")
        out.append({"query": q, "pass": ok, "exit": proc.returncode, "elapsed_s": elapsed,
                    "record": {k: rec.get(k) for k in ("run_id", "outcome", "error_type", "error_stage", "duration_ms")}})
    return out


# ── C2, C4, C5 run in this process so they share one rate limiter ───────────

def c5_two_calls() -> list[dict]:
    from agent import run_agent
    import runlog
    from utils.data_loader import get_example_wardrobe
    out = []
    for q in QUERIES:
        s = run_agent(q, get_example_wardrobe())
        rec = runlog.read()[-1]
        ok = rec["outcome"] == "ok" and rec["model_calls"] == 2
        out.append({"query": q, "pass": ok, "record": {k: rec.get(k) for k in (
            "run_id", "outcome", "model_calls", "prompt_tokens", "output_tokens", "duration_ms", "wait_ms")}})
    return out


def c2_empty() -> list[dict]:
    import config
    from agent import run_agent
    import runlog
    from utils.data_loader import get_example_wardrobe
    out = []
    config.FAULT = "empty"
    try:
        for q in QUERIES:
            s = run_agent(q, get_example_wardrobe())
            rec = runlog.read()[-1]
            item = s["selected_item"] or {}
            card = s["fit_card"] or ""
            usable = bool(card.strip()) and item.get("title", "\0") in card \
                and f"${item.get('price', -1):.2f}" in card
            ok = (rec["outcome"] == "ok_fallback" and "create_fit_card" in rec["fallbacks"] and usable)
            out.append({"query": q, "pass": ok, "fit_card": card, "record": {k: rec.get(k) for k in (
                "run_id", "outcome", "fallbacks", "fault", "model_calls")}})
    finally:
        config.FAULT = ""
    return out


def c4_waiting(max_runs: int = 20) -> list[dict]:
    import generate
    from agent import run_agent
    import runlog
    from utils.data_loader import get_example_wardrobe

    slept = {"s": 0.0}
    real_sleep = time.sleep

    class _TimeShim:  # generate.py calls time.sleep / time.monotonic via `time`
        def __getattr__(self, name):
            return getattr(time, name)

        @staticmethod
        def sleep(seconds):
            t0 = time.perf_counter()
            real_sleep(seconds)
            slept["s"] += time.perf_counter() - t0

    generate.time = _TimeShim()
    out = []
    try:
        for i in range(max_runs):
            slept["s"] = 0.0
            run_agent(QUERIES[i % len(QUERIES)], get_example_wardrobe())
            rec = runlog.read()[-1]
            measured_ms = round(slept["s"] * 1000)
            if measured_ms == 0:
                continue  # this run never hit the limiter; not an attempt
            ok = rec["wait_ms"] > 0 and abs(rec["wait_ms"] - measured_ms) <= 100
            out.append({"query": rec["query"], "pass": ok, "measured_sleep_ms": measured_ms,
                        "record": {k: rec.get(k) for k in ("run_id", "duration_ms", "wait_ms", "stage_ms", "model_calls")}})
            if len(out) == 5:
                break
    finally:
        generate.time = time
    return out


# ── C3 ──────────────────────────────────────────────────────────────────────

def c3_malformed(log: Path) -> list[dict]:
    port = "5081"
    env = {**os.environ, "PORT": port}
    server = subprocess.Popen([PYTHON, "serve.py"], cwd=ROOT, env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    out = []
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(f"http://localhost:{port}/health", timeout=1)
                break
            except Exception:  # noqa: BLE001
                time.sleep(0.5)
        for body in BAD_BODIES:
            n0 = line_count(log)
            req = urllib.request.Request(f"http://localhost:{port}/ask", data=body.encode(),
                                         headers={"Content-Type": "application/json"}, method="POST")
            try:
                status = urllib.request.urlopen(req, timeout=60).status
            except urllib.error.HTTPError as e:
                status = e.code
            time.sleep(0.2)
            recs = new_records(log, n0)
            rejected = [r for r in recs if r.get("outcome") == "rejected"]
            agent_runs = [r for r in recs if r.get("outcome") in ("ok", "ok_fallback", "error", "no_results")]
            ok = status == 400 and len(rejected) == 1 and rejected[0].get("model_calls") == 0 and not agent_runs
            out.append({"body": body, "pass": ok, "http_status": status,
                        "record": rejected[0] if rejected else (recs[-1] if recs else None)})
    finally:
        server.terminate()
        server.wait(timeout=10)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--trial", type=int, required=True)
    args = ap.parse_args()

    log = ROOT / "logs" / f"capstone_{args.label}.jsonl"
    os.environ["AI201_RUN_LOG"] = str(log)
    os.environ["AI201_CACHE"] = "0"
    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)

    started = time.strftime("%Y-%m-%d %H:%M:%S")
    results = {}
    results["C1"] = c1_timeout(log)
    results["C3"] = c3_malformed(log)
    results["C5"] = c5_two_calls()
    results["C2"] = c2_empty()
    results["C4"] = c4_waiting()

    summary = {c: f"{sum(a['pass'] for a in r)}/{len(r)}" for c, r in sorted(results.items())}
    report = {"label": args.label, "trial": args.trial, "started": started, "summary": summary, "attempts": results}
    path = ROOT / "results" / f"capstone_{args.label}_trial{args.trial}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"trial {args.trial} ({args.label}): {summary}  -> {path.name}")


if __name__ == "__main__":
    main()
