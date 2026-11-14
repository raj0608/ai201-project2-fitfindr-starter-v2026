"""
The run log. ← CAPSTONE

One JSON object per agent run, one per line, appended to config.RUN_LOG
(logs/runs.jsonl unless AI201_RUN_LOG says otherwise). `agent.run_agent`
writes it, so the CLI, serve.py and run_eval.py all log the same way, and a
run that failed leaves a record just like one that worked.

Fields, every record:

    ts              when the run finished, UTC, ISO 8601
    run_id          8 hex chars, unique per run
    query           what the user typed
    parsed          {description, size, max_price} pulled from the query
    wardrobe_items  how many items the wardrobe had (0 = empty wardrobe)
    n_results       how many listings search returned
    selected_id     the listing id the agent picked, or null
    outcome         ok | ok_fallback | no_results | error
    error_type      ModelTimeout, EmptyResponse, RateLimited, QuotaGuard,
                    ModelUnavailable, MCPError, ... or null
    error_stage     which step failed: search_listings, suggest_outfit,
                    create_fit_card, agent — or null
    error           the message the user saw, or null
    fallbacks       tools whose empty model answer was replaced by a fallback
    fit_card        the fit card text, or null
    duration_ms     whole run, wall clock
    stage_ms        wall clock per step
    wait_ms         of duration_ms, how much was the rate limiter sleeping
    model_calls     real model requests this run (cache hits not counted)
    cache_hits      answers reused from .cache/
    prompt_tokens   input tokens this run, as reported by the service
    output_tokens   output tokens this run, as reported by the service
    model           config.MODEL
    timeout_s       config.MODEL_TIMEOUT_S in force for this run
    fault           AI201_FAULT in force for this run, or null

The input text and the fit card are logged in full. They're a shopping query
and a caption — nothing in this system is private — and a log you can't read
the output from can't tell you whether the output was any good.
"""

import datetime as dt
import json
import sys
import uuid

import config


def new_run_id() -> str:
    return uuid.uuid4().hex[:8]


def write(record: dict) -> None:
    """
    Append one record. Never raises: a full disk or a bad path should cost the
    log line, not the user's answer.
    """
    record = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds"), **record}
    try:
        config.RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
        with config.RUN_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception as exc:  # noqa: BLE001
        print(f"  [runlog] couldn't write {config.RUN_LOG}: {exc}", file=sys.stderr, flush=True)


def read(path=None) -> list[dict]:
    """Every record in the log, oldest first. Skips lines that don't parse."""
    path = path or config.RUN_LOG
    records = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        pass
    return records
