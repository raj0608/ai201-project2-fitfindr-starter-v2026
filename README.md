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

Produced by `python run_eval.py --label before` (writes
`results/run_2026-10-07_1852_before.md`, 14 scenarios × 5 tries, cache off,
130 model calls) plus two supplementary checks for criteria 3 and 5, which
need more than the generic session dump captures — see each criterion's note.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before tool 2 | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. selected_item id matches what suggest_outfit receives | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card: price mentioned (5/5) + no shared opening sentence (5 items) | 5 of 5 each | price PASS, opening PASS | price PASS, opening PASS | price PASS, opening PASS | price PASS, opening **FAIL** | price PASS, opening **FAIL** | MISSED (price 5/5, openings 4 distinct of 5) |
| 5. Every search result respects max_price (5 ceilings) | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Criterion 1 — real output**, from `agent.py::run_agent`, `scenarios.py` scenario "matching query completes", try 1 (`results/run_2026-10-07_1852_before.md` lines 47-81):

```
Query: vintage graphic tee under $30

- stopped early: no
- selected_item: Y2K Baby Tee — Butterfly Print ($18.0, depop)
- search_results: 10

Fit card:
Scored this gorgeous Y2K butterfly baby tee on Depop for just $18 and I'm literally obsessed. The pastel print gives off the cutest nostalgic energy, especially when I balance it out with baggy denim and chunky boots. Absolute win for the rotation!
```

**Criterion 2 — real output**, from `agent.py::run_agent`, scenario "impossible query stops early", try 1 (same file, lines 232-248):

```
Query: designer ballgown size XXS under $5

- stopped early: yes — No listings matched that description, size, and price. Try a plainer description, a higher max_price, or dropping the size.
- selected_item: (none)
- search_results: 0

Trace:
[1] parse_query
[2] search_listings (via MCP)
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit
```

**Criterion 3 — real output**, from a supplementary script that monkeypatches `tools.suggest_outfit` to record the id it receives, then compares it to `session["selected_item"]["id"]` — the generic run_eval session dump doesn't expose what a tool was actually called with, only what the session holds:

```
Try 1: query='vintage graphic tee under $30'
        session['selected_item']['id'] = 'lst_002'
        id suggest_outfit received      = 'lst_002'
        PASS
Try 2: query='90s track jacket in size M'           -> 'lst_004' == 'lst_004'  PASS
Try 3: query='silk slip dress in midi length under $40' -> 'lst_013' == 'lst_013'  PASS
Try 4: query='platform sneakers size 8'             -> 'lst_019' == 'lst_019'  PASS
Try 5: query='denim jacket under $50'               -> 'lst_007' == 'lst_007'  PASS

Overall: 5 of 5 PASS
```

**Criterion 4 — real output**, the five fit cards (try 1 of each of the five `fit card N` scenarios, `results/run_2026-10-07_1852_before.md` lines 702-1636):

```
1. graphic tee ($18):  "Found the holy grail on Depop today—an absolute mint-condition Y2K
   butterfly baby tee for just $18! ..."
2. track jacket ($45.00): "Score! Found this navy and white 90s track jacket on Poshmark
   for just $45.00 and it's in mint condition. ..."
3. slip dress ($30): "Obsessed is an understatement for this 90s silk slip dress I just
   scored on Depop for only $30. ..."
4. sneakers ($48): "My inner 90s model-off-duty just screamed. Snagged these platform
   sneakers on Poshmark for $48 ..."
5. denim jacket ($42): "Score! 🤩 Just snagged this cropped light-wash denim jacket on
   Poshmark for only $42 and the condition is unreal. ..."
```

Every card mentions its item's exact price — 5 of 5. But cards 2 and 5 both open
with the bare interjection **"Score!"** before anything else — an exact duplicate
opening, confirmed by splitting each card on its first sentence-ending punctuation.

**Criterion 5 — real output**, from `tools.py::search_listings` directly (price filtering doesn't touch the model, so no cache/trace involved):

```
Try 1: description='tops'        max_price=20.0 -> 7 results, prices=[18.0, 20.0, 15.0, 16.0, 18.0, 19.0, 17.0]  PASS
Try 2: description='bottoms'     max_price=30.0 -> 6 results, prices=[27.0, 30.0, 24.0, 29.0, 14.0, 30.0]        PASS
Try 3: description='outerwear'   max_price=45.0 -> 6 results, prices=[45.0, 42.0, 40.0, 38.0, 33.0, 27.0]        PASS
Try 4: description='shoes'       max_price=50.0 -> 3 results, prices=[48.0, 44.0, 20.0]                         PASS
Try 5: description='accessories' max_price=15.0 -> 2 results, prices=[12.0, 14.0]                               PASS

Overall: 5 of 5 PASS
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
| 1 | Matching query completes all three tools | 4 of 5 | MET (5/5) | Counted PASS where `search_results` was non-empty and `fit_card` was produced; all 5 tries completed. |
| 2 | Impossible query stops before tool 2 | 5 of 5 | MET (5/5) | Counted PASS where `session["error"]` was set and `fit_card` stayed `None`; all 5 tries stopped at the branch. |
| 3 | selected_item id matches what suggest_outfit receives | 5 of 5 | MET (5/5) | Compared `session["selected_item"]["id"]` against the id a patched `suggest_outfit` actually received, across 5 different matching queries; identical every time. |
| 4 | Fit card mentions exact price (5/5) and no two of 5 share an opening sentence | 5 of 5 each | **MISSED** (price 5/5, openings 4 distinct of 5) | Checked each of the 5 different-item fit cards for the item's exact price string — present in all 5. Split each card on its first sentence-ending punctuation and compared the 5 openings — 2 of 5 (track jacket and denim jacket) were both the bare word "Score!", an exact duplicate. |
| 5 | Every search result respects max_price | 5 of 5 | MET (5/5) | Ran `search_listings` with 5 different price ceilings, one per category, and checked every returned price against its ceiling directly; no violations across 25 total listings checked. |

**Diagnoses**

Criterion 4 is the only miss, and it's one mechanism, not several: the
`create_fit_card` prompt in `tools.py` (lines 224-233) asks for a caption that
"sounds like a real person's post" and names the vibe, but never tells the
model to avoid opening with a stock reaction word. At `TEMPERATURE = 0.9`
that's enough to get real variation in most of the sentence, but the model
still has a small, high-probability set of generic openers ("Score!", "Found",
"Scored") it reaches for before it starts describing anything — and with only
5 samples, two landing on the exact same one-word opener isn't surprising.

This is the model's output, not the tool or the loop — `search_listings` and
the branch in `run_agent` are unaffected (criteria 1, 2, 3, 5 all hold at
5/5), and the price is being inserted into every card exactly as asked.
The prompt simply doesn't rule out a generic opening, so it doesn't always
avoid one. This is the miss I'm fixing in **The Improvement**, below.

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Failure modes triggered on purpose**

1. *Empty search* — `python app.py ask 'designer ballgown size XXS under $5'`:
   ```
   No listings matched that description, size, and price. Try a plainer description, a higher max_price, or dropping the size.
   ```
   Already handled going into this unit — the branch rule from Unit 3 covers it.

2. *Empty wardrobe* — `python app.py ask 'denim jacket under $50' --empty-wardrobe`: returned real general styling advice ("A light-wash cropped denim jacket is a versatile wardrobe staple that instantly adds effortless cool to any outfit...") instead of a crash or an empty string. Already handled by the `if not items:` branch in `tools.py::suggest_outfit` from Unit 3.

3. *Model unavailable* — changed one character of `GEMINI_API_KEY` in `.env`, then ran a query the cache had never seen (`'silk slip dress in midi length under $40 for a totally novel phrasing xyz123'`):
   ```
   The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.
   ```
   This one **was not handled** before this unit — `run_agent` didn't catch `ModelUnavailable`, so it would have propagated up as an uncaught exception. Added a `try/except ModelUnavailable` around both the `suggest_outfit` and `create_fit_card` calls in `agent.py::run_agent`, each setting `session["error"]` and returning early, the same shape as the empty-search branch. Restored the real key afterward and confirmed `python test.py` passes again.

**Happy path**

```
$ python app.py ask 'vintage graphic tee under $30' --trace
[1] parse_query
      in:  dict with keys: query
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    branch: match found, continuing
[3] suggest_outfit
      in:  dict with keys: item, wardrobe_items
      out: Pair the Y2K butterfly baby tee with your baggy dark-wash straight-leg jeans to nail that classic high-low pro…
[4] create_fit_card
      in:  dict with keys: outfit, item
      out: Obsessed with this Y2K butterfly baby tee I just scored on Depop for only $18! The print is giving total early…

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Pair the Y2K butterfly baby tee with your baggy dark-wash straight-leg jeans to nail that classic high-low proportion play. Throw on your black cropped zip hoodie and chunky white sneakers to lean fully into the nostalgic 2000s aesthetic.

  Fit card: Obsessed with this Y2K butterfly baby tee I just scored on Depop for only $18! The print is giving total early 2000s pop star off-duty, especially paired with baggy dark wash denim and chunky sneakers. Such a good addition to the rotation.
```

**Empty search**

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace
[1] parse_query
      in:  dict with keys: query
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit

  No listings matched that description, size, and price. Try a plainer description, a higher max_price, or dropping the size.
```

**On the MCP move:** Moved `search_listings` behind MCP — it was the natural
pick since it doesn't call the model. Registered it in `mcp_server.py` with a
docstring written for a reader who can't see the implementation (names the
size-matching rule and the empty-list contract explicitly, since a different
agent can't infer either from code it'll never see). In `agent.py::run_agent`,
the direct call `search_listings(description=..., size=..., max_price=...)`
became `call_tool("search_listings", {...})`, imported from `mcp_client`
instead of `tools`. `suggest_outfit` and `create_fit_card` are unchanged —
still direct calls into `tools.py`.

Nothing behaved differently afterward. Ran both the matching and empty-search
example queries before and after the rewire and got identical output both
times — same selected item, same branch taken on the impossible query. That's
the expected result: MCP changes how the call is made, not what comes back.

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
