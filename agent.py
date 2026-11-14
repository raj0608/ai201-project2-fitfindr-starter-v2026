"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re
import time

import config
import generate
import runlog
import trace
from mcp_client import call_tool, MCPError
from tools import suggest_outfit, create_fit_card
from generate import (
    EmptyResponse,
    ModelTimeout,
    ModelUnavailable,
    QuotaGuard,
    RateLimited,
)

_PRICE_PATTERN = re.compile(r"under\s*\$?\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
_SIZE_PATTERN = re.compile(r"size\s+([A-Za-z0-9/.\-]+)", re.IGNORECASE)


def _parse_query(query: str) -> dict:
    """
    Pull a max_price and a size out of a free-text query, regex-based.

    "vintage graphic tee under $30" -> description="vintage graphic tee",
    size=None, max_price=30.0
    "90s track jacket in size M"    -> description="90s track jacket",
    size="M", max_price=None
    """
    price_match = _PRICE_PATTERN.search(query)
    max_price = float(price_match.group(1)) if price_match else None

    size_match = _SIZE_PATTERN.search(query)
    size = size_match.group(1) if size_match else None

    description = _PRICE_PATTERN.sub("", query)
    description = _SIZE_PATTERN.sub("", description)
    description = re.sub(r"\bin\b", " ", description, flags=re.IGNORECASE)
    description = re.sub(r"\s+", " ", description).strip(" ,")

    return {"description": description, "size": size, "max_price": max_price}


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
        # capstone — what went wrong, where, and what was papered over
        "error_type": None,          # e.g. "ModelTimeout" — None on success
        "error_stage": None,         # which step failed
        "fallbacks": [],             # tools whose empty answer got a fallback
        "stage_ms": {},              # wall-clock time per step
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.

    CAPSTONE: this wrapper is the hardening layer. Whatever happens inside the
    loop — a timeout, an empty answer, a rate limit that never lifts, the
    session budget, or a bug — run_agent returns a session with
    session["error"] set rather than raising, and every run, good or bad,
    writes one record to the run log (runlog.py).
    """
    session = new_session(query, wardrobe)
    run_id = runlog.new_run_id()
    before = _usage_snapshot()
    started = time.perf_counter()

    try:
        _run_loop(session, wardrobe)
    except _Stop:
        pass  # a handled failure — session["error"] is already set
    except Exception as exc:  # noqa: BLE001 — the last line of defence
        _fail(
            session, "agent", exc,
            f"Something went wrong inside FitFindr ({type(exc).__name__}: {exc}). "
            f"Try again, and if it repeats, "
            f"run with --trace to see which step it stopped at.",
        )

    duration_ms = round((time.perf_counter() - started) * 1000)
    after = _usage_snapshot()
    runlog.write(_log_record(session, run_id, duration_ms, before, after))
    return session


# ── capstone: failure handling ────────────────────────────────────────────────

class _Stop(Exception):
    """Internal: a step failed in a way we handled; unwind to run_agent."""


def _fail(session: dict, stage: str, exc: Exception, message: str) -> None:
    session["error"] = message
    session["error_type"] = type(exc).__name__
    session["error_stage"] = stage
    trace.step(stage, note=f"{type(exc).__name__}: stopping")


def _model_failure_message(exc: Exception, stage: str) -> str:
    """What the user reads when a model step fails, by failure type."""
    if isinstance(exc, ModelTimeout):
        return (
            f"The stylist model didn't answer within {config.MODEL_TIMEOUT_S:g}s "
            f"while running {stage}, so FitFindr stopped instead of leaving you "
            f"waiting. Try again in a moment."
        )
    if isinstance(exc, RateLimited):
        return (
            f"The model is rate-limiting this API key and kept refusing after "
            f"{config.MAX_RETRIES} attempts during {stage}. Wait a minute and "
            f"ask again — your key is fine."
        )
    if isinstance(exc, QuotaGuard):
        return (
            f"This session has used its request budget "
            f"({config.SESSION_REQUEST_BUDGET} model calls, SESSION_REQUEST_BUDGET "
            f"in config.py), so FitFindr stopped before {stage}. Restart to reset it."
        )
    return str(exc)  # ModelUnavailable already carries a readable message


def _model_step(session: dict, stage: str, call, fallback):
    """
    Run one model-backed tool. An empty answer gets the fallback (and is noted
    in session["fallbacks"]); any other model failure stops the run.
    """
    t0 = time.perf_counter()
    try:
        return call()
    except EmptyResponse:
        session["fallbacks"].append(stage)
        trace.step(stage, note="model returned empty text, using fallback")
        return fallback()
    except (ModelUnavailable, RateLimited, QuotaGuard) as exc:
        _fail(session, stage, exc, _model_failure_message(exc, stage))
        raise _Stop from exc
    finally:
        session["stage_ms"][stage] = round((time.perf_counter() - t0) * 1000)


def _outfit_fallback(item: dict) -> str:
    return (
        f"Pair the {item['title']} with whatever you already reach for most — "
        f"it's a versatile enough piece to work on its own."
    )


def _fit_card_fallback(item: dict) -> str:
    """Deterministic caption: always names the item, its price, and platform."""
    return (
        f"{item['title']}, {item['condition']} condition — ${item['price']:.2f} "
        f"on {item['platform'].capitalize()}. Thrifted, and ready to wear."
    )


def _usage_snapshot() -> dict:
    tokens = generate.token_counts()
    return {
        "calls": generate.call_count(),
        "cache_hits": generate._cache_hits,
        "prompt": tokens["prompt"],
        "output": tokens["output"],
        "wait": generate.wait_seconds(),
    }


def _log_record(session, run_id, duration_ms, before, after) -> dict:
    if session["error"]:
        outcome = "no_results" if session["error_type"] == "NoResults" else "error"
    elif session["fallbacks"]:
        outcome = "ok_fallback"
    else:
        outcome = "ok"
    item = session["selected_item"] or {}
    return {
        "run_id": run_id,
        "query": session["query"],
        "parsed": session["parsed"],
        "wardrobe_items": len((session["wardrobe"] or {}).get("items", [])),
        "n_results": len(session["search_results"] or []),
        "selected_id": item.get("id"),
        "outcome": outcome,
        "error_type": None if outcome == "no_results" else session["error_type"],
        "error_stage": session["error_stage"],
        "error": session["error"],
        "fallbacks": session["fallbacks"],
        "fit_card": session["fit_card"],
        "duration_ms": duration_ms,
        "stage_ms": session["stage_ms"],
        "wait_ms": round((after["wait"] - before["wait"]) * 1000),
        "model_calls": after["calls"] - before["calls"],
        "cache_hits": after["cache_hits"] - before["cache_hits"],
        "prompt_tokens": after["prompt"] - before["prompt"],
        "output_tokens": after["output"] - before["output"],
        "model": config.MODEL,
        "timeout_s": config.MODEL_TIMEOUT_S,
        "fault": config.FAULT or None,
    }


# ── the loop itself (units 3-4, unchanged except where marked) ───────────────

def _run_loop(session: dict, wardrobe: dict) -> None:
    query = session["query"]
    count = 0

    count += 1
    trace.check_iterations(count)
    session["parsed"] = _parse_query(query)
    trace.step("parse_query", inputs={"query": query}, returned=session["parsed"])

    count += 1
    trace.check_iterations(count)
    t0 = time.perf_counter()
    try:
        session["search_results"] = call_tool("search_listings", {
            "description": session["parsed"]["description"],
            "size": session["parsed"]["size"],
            "max_price": session["parsed"]["max_price"],
        })
    except MCPError as exc:
        session["stage_ms"]["search_listings"] = round((time.perf_counter() - t0) * 1000)
        _fail(
            session, "search_listings", exc,
            f"Couldn't reach the search tool: {exc}\n"
            f"Check that mcp_server.py runs on its own: python mcp_server.py",
        )
        raise _Stop from exc
    session["stage_ms"]["search_listings"] = round((time.perf_counter() - t0) * 1000)

    if not session["search_results"]:
        session["error"] = (
            "No listings matched that description, size, and price. Try a "
            "plainer description, a higher max_price, or dropping the size."
        )
        session["error_type"] = "NoResults"   # capstone: the branch, not a failure
        trace.step(
            "search_listings (via MCP)",
            inputs=session["parsed"],
            returned=session["search_results"],
            note="branch: empty, stopping before suggest_outfit",
        )
        return

    session["selected_item"] = session["search_results"][0]
    trace.step(
        "search_listings (via MCP)",
        inputs=session["parsed"],
        returned=session["search_results"],
        note="branch: match found, continuing",
    )
    item = session["selected_item"]

    count += 1
    trace.check_iterations(count)
    session["outfit_suggestion"] = _model_step(
        session, "suggest_outfit",
        lambda: suggest_outfit(item, wardrobe),
        lambda: _outfit_fallback(item),
    )
    trace.step(
        "suggest_outfit",
        inputs={"item": item["id"], "wardrobe_items": len(wardrobe.get("items", []))},
        returned=session["outfit_suggestion"],
    )

    count += 1
    trace.check_iterations(count)
    session["fit_card"] = _model_step(
        session, "create_fit_card",
        lambda: create_fit_card(session["outfit_suggestion"], item),
        lambda: _fit_card_fallback(item),
    )
    trace.step(
        "create_fit_card",
        inputs={"outfit": session["outfit_suggestion"], "item": item["id"]},
        returned=session["fit_card"],
    )


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
