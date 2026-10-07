"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # A user with nothing saved. One of unit 4's three failure modes.
        "name": "empty wardrobe",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": None,
    },
    {
        # Criterion 3 — state. A normal matching query; what's checked isn't
        # the query, it's whether session["selected_item"]'s id matches the
        # id suggest_outfit actually received. The generic session dump below
        # doesn't capture that by itself — see the supplementary check script
        # described under criterion 3 in the README's Run Log.
        "name": "state: selected item reaches suggest_outfit",
        "query": "90s track jacket in size M",
        "wardrobe": "example",
        "criterion": 3,
    },
    # Criterion 4 needs 5 DIFFERENT items, not the same query 5 times — each
    # of these is run once (see the supplementary script in the README).
    {"name": "fit card 1: graphic tee", "query": "vintage graphic tee under $30", "wardrobe": "example", "criterion": 4},
    {"name": "fit card 2: track jacket", "query": "90s track jacket in size M", "wardrobe": "example", "criterion": 4},
    {"name": "fit card 3: slip dress", "query": "silk slip dress in midi length under $40", "wardrobe": "example", "criterion": 4},
    {"name": "fit card 4: sneakers", "query": "platform sneakers size 8", "wardrobe": "example", "criterion": 4},
    {"name": "fit card 5: denim jacket", "query": "denim jacket under $50", "wardrobe": "example", "criterion": 4},
    # Criterion 5 needs 5 DIFFERENT price ceilings, one per category so each
    # actually returns results worth checking.
    {"name": "price ceiling 1: tops $20", "query": "tops under $20", "wardrobe": "example", "criterion": 5},
    {"name": "price ceiling 2: bottoms $30", "query": "bottoms under $30", "wardrobe": "example", "criterion": 5},
    {"name": "price ceiling 3: outerwear $45", "query": "outerwear under $45", "wardrobe": "example", "criterion": 5},
    {"name": "price ceiling 4: shoes $50", "query": "shoes under $50", "wardrobe": "example", "criterion": 5},
    {"name": "price ceiling 5: accessories $15", "query": "accessories under $15", "wardrobe": "example", "criterion": 5},
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
