# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

A user describes what they want in plain language — "a vintage graphic tee
under $30, size M" — and FitFindr searches the listings data for matches,
picks the best one, figures out what it would go with from the user's saved
wardrobe, and writes a short caption someone would actually post about the
find. If nothing in the data matches, it says so and stops instead of
guessing.

---

## Tool Inventory

### `search_listings`

- **What it does:** Filters the listings data by price and size, scores what's left by keyword overlap with the description, and returns the best matches.
- **Inputs:** `description` (str) — free-text keywords, e.g. "vintage graphic tee". `size` (str or None) — a size string to filter by; None skips size filtering. `max_price` (float or None) — inclusive price ceiling; None skips price filtering.
- **Returns:** A list of listing dicts (`id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`), best match first, capped at `config.SEARCH_RESULT_LIMIT`.
- **When it has nothing:** An empty list — never `None`, never an exception.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfit ideas combining a new item with the user's saved wardrobe.
- **Inputs:** `new_item` (dict) — a listing dict, the item under consideration. `wardrobe` (dict) — a wardrobe dict with an `items` key holding a list of wardrobe item dicts; may be empty.
- **Returns:** A non-empty string of outfit suggestions, naming specific wardrobe pieces by name when the wardrobe isn't empty.
- **When it has nothing:** An empty wardrobe isn't an error — it gets general styling advice for the item instead of pairing suggestions. If the model somehow returns nothing, a hardcoded fallback sentence is returned instead of an empty string.

### `create_fit_card`

- **What it does:** Writes a short, postable caption for the item using the outfit suggestion.
- **Inputs:** `outfit` (str) — the string `suggest_outfit()` returned. `new_item` (dict) — the listing dict for the item.
- **Returns:** A 2-4 sentence caption string that mentions the item, its price, and its platform once each.
- **When it has nothing:** If `outfit` is empty or whitespace-only, returns a plain descriptive sentence about the item instead of calling the model or raising.

---

## Planning Loop

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` naming what to change (description, size, or price) and stop — do not call `suggest_outfit`. Otherwise, take the first result as `session["selected_item"]` and continue to `suggest_outfit` and then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex. `agent.py::_parse_query` pulls a price ceiling out of a `"under $N"` pattern and a size out of a `"size X"` pattern, strips both (plus the leftover word "in") out of the query, and treats what's left as the description.

**What moves through the session:** `parsed` → `search_results` → `selected_item` → `outfit_suggestion` → `fit_card`, in that order. Each tool reads its input from the session field the previous tool wrote, rather than from a local variable.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Pair the Y2K butterfly baby tee with your baggy dark-wash straight-leg jeans to nail that classic high-low proportion play. Throw on your black cropped zip hoodie and chunky white sneakers to lean fully into the nostalgic 2000s aesthetic.

  Fit card: Obsessed with this Y2K butterfly baby tee I just scored on Depop for only $18! The print is giving total early 2000s pop star off-duty, especially paired with baggy dark wash denim and chunky sneakers. Such a good addition to the rotation.

2 model calls this session, 357 prompt + 112 output tokens
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'price': 18.0, 'size': 'S/M', ...},
 {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'price': 24.0, 'size': 'L', ...},
 ... 6 results total, best keyword match first, all priced $30 or under
```

```
$ python -c "
from tools import suggest_outfit
from utils.data_loader import get_example_wardrobe, load_listings
print(suggest_outfit(load_listings()[0], get_example_wardrobe()))
"
Pair the vintage medium-wash Levi's with the white ribbed tank top and the vintage black denim jacket for a classic, textured contrast, then ground the look with your black combat boots and the black crossbody bag. Add the brown leather belt to tie the look together with a subtle warm accent.
```

```
$ python -c "
from tools import create_fit_card
from utils.data_loader import load_listings
print(create_fit_card('Pair with a white tank top and black combat boots.', load_listings()[0]))
"
Manifested these vintage Levi's 501 jeans on Depop and still can't believe they were only $38. They've got that *exact* 90s slouch I've been hunting for forever. Just throwing them on with a white tank and black combat boots for the ultimate effortless weekend uniform.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* Help designing the size-matching logic for `search_listings` so a query for size "M" matches listing sizes like "S/M" and "M/L" but not "XL" or "US 9".
- *What came back:* A token-based match — strip any parenthetical note off the listing's size string, split what's left on slashes and spaces, and check whether the query size equals a whole token (or the whole normalized string, for phrases like "One Size").
- *What I changed:* Nothing in the approach — I ran it against every distinct size value in `data/listings.json` by hand (`"L" matches "XL"?` → False, `"M" matches "S/M"?` → True) before trusting it, since the docstring specifically calls out that a plain substring test passes both of those wrong.

**Moment 2**

- *What I asked for:* How to turn a free-text query like "90s track jacket in size M" into `description`/`size`/`max_price` without spending a model call on something this mechanical.
- *What came back:* Two regexes — one for `under $N`, one for `size X` — pulled out first, with whatever's left over treated as the description.
- *What I changed:* The first pass left a stray "in" in descriptions like "track jacket in size M" once the size phrase was stripped out, so I added a step to drop the standalone word "in" too, rather than letting it sit in the keyword set that `search_listings` scores against.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
