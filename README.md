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

**Moment 3 (Unit 4)**

- *What I asked for:* After the Before run, I had 5 fit cards for criterion 4 and wasn't sure whether 2 of them really counted as sharing an "opening sentence" — one pair both started with "Score!" but the rest of the sentence differed. I asked for the opposite case: an argument that they *don't* actually violate the criterion.
- *What came back:* The strongest version of that argument is that "opening sentence" should mean the first substantive clause, not a one-word interjection — by that reading, "Score!" isn't a sentence, it's punctuation-adjacent filler, and the two cards' real openings ("Found this..." vs. "Just snagged...") are distinct.
- *What I changed:* Nothing — I kept the stricter, literal reading (first run of text up to the first sentence-ending punctuation) because that's what I'd actually written in `criteria.md`, and loosening the definition after seeing an inconvenient result is exactly the kind of after-the-fact criterion-softening the brief says not to do. I verified it programmatically (splitting on `.`/`!`/`?`) rather than trusting my own eyeballing, which is what caught the duplicate in the first place.

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

**What I changed:** One sentence added to the `create_fit_card` prompt in
`tools.py` (around line 230): *"Don't open with a generic reaction word like
'Score!', 'Found', or 'Scored' — start the first sentence with something
specific to this item instead, like its color, print, era, or fabric."*
Nothing else in `tools.py`, `agent.py`, or `mcp_server.py` changed.

**Which failure it was meant to fix:** Criterion 4's opening-sentence miss
from the Before run — 2 of 5 fit cards (track jacket, denim jacket) both
opened with the exact same bare interjection, "Score!".

### Run Log — After

Produced by `python run_eval.py --label after` (writes
`results/run_2026-10-07_1903_after.md`, same 14 scenarios × 5 tries, cache
off, 130 model calls).

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before tool 2 | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. selected_item id matches what suggest_outfit receives | 5 of 5 | — | — | — | — | — | MET (5/5, unaffected — neither `agent.py` nor `search_listings`/`suggest_outfit` changed) |
| 4. Fit card: price mentioned (5/5) + no shared opening sentence | 5 of 5 each | price PASS, opening PASS | price PASS, opening PASS | price **FAIL**, opening PASS | price PASS, opening PASS | price PASS, opening PASS | MISSED (openings 5/5 fixed; price now 4/5) |
| 5. Every search result respects max_price | 5 of 5 | — | — | — | — | — | MET (5/5, unaffected — `search_listings` wasn't touched) |

Criteria 3 and 5 weren't re-run with fresh model calls — the only change this
unit touches is `create_fit_card`'s prompt, and neither criterion exercises
that function, so re-running them would just reproduce the identical Before
result at the cost of more quota.

**Real output — the five fit cards, try 1 of each item scenario**
(`results/run_2026-10-07_1903_after.md`, lines 702-1636):

```
1. graphic tee ($18):  "That little butterfly print is just pure early 2000s
   magic, and I honestly can't believe I snagged this Y2K baby tee on Depop
   for only $18. ..."
2. track jacket ($45.00): "That crisp navy and white stripe is screaming
   major 90s nostalgia. I couldn't pass up this vintage track jacket for
   just $45.00 once I spotted it on Poshmark. ..."
3. slip dress ($30): "Ditsy florals and liquid silk scream peak 90s, so I
   had to grab this midi slip dress when I saw it on Depop. For just thirty
   bucks, it's practically begging to be worn ... ..."
4. sneakers ($48): "Crisp white leather and a chunky sole are about to
   become my entire personality. Snagged these platform sneakers on
   Poshmark for just $48 ..."
5. denim jacket ($42): "That breezy light wash denim jacket I just snagged
   on Poshmark is honestly the ultimate throw-on-and-go piece. For only
   $42 ..."
```

**Did it help, and how do I know:** Partly. The targeted failure is fixed —
all 5 openings are distinct now (verified the same way as Before: split each
card on its first sentence-ending punctuation and compared), where Before had
an exact duplicate. But the same run surfaced a different, previously-unseen
miss on the same criterion: card 3 (slip dress) wrote the price as "thirty
bucks" instead of a digit form like "$30", which fails the strict
price-mention check I wrote ("$24.00" or "24"). I didn't cause this by
editing the prompt — the prompt never specified digit form either before or
after — it's a case the Before run's 5 samples simply didn't happen to hit.
So: the opening-sentence sub-check went from MISSED to MET, and the
price-mention sub-check went from MET (5/5) to MISSED (4/5), on the same
criterion, in the same run. Net result: criterion 4 is still MISSED overall,
but the mechanism behind the miss changed, which is itself useful information
— see What's Still Broken.

---

## What's Still Broken

Criterion 4 (fit card) is still MISSED after one improvement, though the
specific sub-check that fails changed:

**The price-mention sub-check (now 4 of 5).** The prompt asks the model to
"mention... the price" but never says in what form. Spelling it out
("thirty bucks") satisfies a human reader fine but fails my strict
digit-form check. What I'd do next: add one more sentence to the prompt —
"Write the price as a dollar figure like '$30', not spelled out" — and
re-run. I stopped here because this unit caps me at one measured change, and
I'd rather report this honestly as a new, smaller, separately-diagnosed miss
than fold it into the same "improvement" and muddy which fix did what.

**The underlying tension.** Both misses (the original duplicate opener and
this one) come from the same root cause: the prompt constrains content
("mention the price," "be specific about the vibe") but not *form* ("as a
digit," "not a stock phrase"), and at `TEMPERATURE = 0.9` the model is free
to vary in ways I haven't ruled out. Each fix I add closes one gap and, on 5
samples, there's a reasonable chance another one I haven't anticipated shows
up. A sturdier long-term fix would be validating the fit card's shape in code
after generation (check for a `$` digit sequence, re-prompt or fall back if
missing) rather than only steering the prompt — I didn't attempt that here
because it's a tool-logic change, and this unit's rule was one change,
measured properly.



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

---

## Capstone

**What This Extends**

FitFindr, the thrift-shopping agent from units 3–4. It parses a query,
searches listings over MCP, then makes two Gemini calls (`suggest_outfit`,
`create_fit_card`) to write an outfit idea and a fit card. What's new this
unit is a hardened model-call stage, structured per-run logging, and a
documented local run path.

**The Shape**

B — harden against failure. FitFindr works when Gemini answers, and only
then. I checked before scoping, with the model call stubbed out: an empty
model response produces an empty fit card (`''`), and both `QuotaGuard` and
the "still rate limited after 5 attempts" `RuntimeError` escape
`agent.py::run_agent` as uncaught exceptions — so the CLI prints a crash and
`serve.py` returns a 500. There is also no timeout on the Gemini call, so a
stalled request hangs the run forever. The extension is one hardening layer
on the model-call stage (`generate.py` and the two tools behind it): a request
timeout, an empty-response guard, and handling in `run_agent` so that every
model-stage failure ends the run with a readable `session["error"]` and a
log record instead of a crash, a hang, or a blank fit card. A small
fault-injection switch lets me trigger each failure on purpose.

Out of scope, on purpose:

- **Not touching search or MCP.** `search_listings` has no model in it and
  `MCPError` is already handled; the bad path I'm hardening is the model one.
- **Not editing the prompts.** The "thirty bucks" price miss from unit 4 is a
  prompt/output-quality problem, not a failure-handling one.
- **Not hosting it or making `serve.py` concurrent.** This runs on Path B
  (local with logs), and the one-request-at-a-time lock stays as it is.

**Running It**

Path B — local with logs. One command starts it (`python serve.py`), and
[RUNNING.md](RUNNING.md) has the full run path at the top under "Capstone run
path": Python 3.13.15, exact pins in `requirements-lock.txt`, no model files,
one API key. I tested those instructions by cloning the repo into an empty
folder, building a fresh venv from the lockfile, and starting the server:
`test.py` passed 10/10, a `POST /ask` came back with a fit card, and
`logs/runs.jsonl` was created from nothing with a record of it. I didn't host
it — no local model, so the 512 MB tier would fit, but the signup wants a card.

**Instrumentation**

Every agent run writes one JSON line to `logs/runs.jsonl`. The writer is
`runlog.py::write`, called from the end of `agent.py::run_agent` — so the CLI,
`serve.py` and `run_eval.py` all log the same way, and a run that fails is
logged on its way out exactly like one that worked. `serve.py::ask` writes its
own record for the one case that never reaches `run_agent`: a request it
rejects with a 400.

What each record holds (full list at the top of `runlog.py`): `ts`, `run_id`,
`query`, `parsed`, `wardrobe_items`, `n_results`, `selected_id`, `outcome`
(`ok`, `ok_fallback`, `no_results`, `error`, `rejected`), `error_type`,
`error_stage`, `error` (the message the user saw), `fallbacks`, `fit_card`,
`duration_ms`, `stage_ms` (per step), `wait_ms` (how much of the duration was
the rate limiter sleeping), `model_calls`, `cache_hits`, `prompt_tokens`,
`output_tokens`, `model`, `timeout_s`, and `fault`.

The two fields I'd have skipped without thinking about it are `wait_ms` and
`fault`. `wait_ms` matters because this client paces itself to 15 requests a
minute — without it, a run that sat 47 seconds in the limiter looks exactly
like a slow model. `fault` matters because half my bad-path records are
injected on purpose, and a log that doesn't say so would read like an outage.

The full committed record, all 21 entries from one session on 2026-11-14.
The first 10 are the cost runs (`python measure_cost.py`). The rest are one of
each bad path triggered on purpose, one empty-wardrobe run, and four malformed
requests to `serve.py` (`{}`, `{"query": 123}`, `[1,2]`, `not json`):

```jsonl
{"ts": "2026-11-14T10:03:17.067+00:00", "run_id": "1f0c53df", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "wardrobe_items": 10, "n_results": 10, "selected_id": "lst_002", "outcome": "ok", "error_type": null, "error_stage": null, "error": null, "fallbacks": [], "fit_card": "That dreamy butterfly print totally screams peak 2-4-7 Y2K energy. Snagged this baby tee off Depop for just $18 and the fit is honestly unreal. Pair it with low-rise baggy denim and chunky sneakers for the ultimate off-duty pop star vibe.", "duration_ms": 2272, "stage_ms": {"search_listings": 391, "suggest_outfit": 1088, "create_fit_card": 793}, "wait_ms": 0, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 410, "output_tokens": 121, "model": "gemini-3.5-flash-lite", "timeout_s": 20.0, "fault": null}
{"ts": "2026-11-14T10:03:18.665+00:00", "run_id": "20266e6c", "query": "90s track jacket in size M", "parsed": {"description": "90s track jacket", "size": "M", "max_price": null}, "wardrobe_items": 10, "n_results": 4, "selected_id": "lst_004", "outcome": "ok", "error_type": null, "error_stage": null, "error": null, "fallbacks": [], "fit_card": "Crisp navy with sporty white stripes, this 90s track jacket just came in from Poshmark and it is *so* off-duty model-off-duty. Snagged it for $45 and the condition is literally pristine. Throwing it over baggy denim and chunky sneakers ASAP.", "duration_ms": 1597, "stage_ms": {"search_listings": 233, "suggest_outfit": 657, "create_fit_card": 706}, "wait_ms": 0, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 432, "output_tokens": 142, "model": "gemini-3.5-flash-lite", "timeout_s": 20.0, "fault": null}
{"ts": "2026-11-14T10:03:20.691+00:00", "run_id": "728cad54", "query": "silk slip dress in midi length under $40", "parsed": {"description": "silk slip dress midi length", "size": null, "max_price": 40.0}, "wardrobe_items": 10, "n_results": 5, "selected_id": "lst_013", "outcome": "ok", "error_type": null, "error_stage": null, "error": null, "fallbacks": [], "fit_card": "That dreamy 90s floral silk slip dress finally arrived from Depop and it was totally worth the $30. Layering it over a white ribbed tank with chunky sneakers is my new go-to daytime uniform, but it's gonna look so good with combat boots and a denim jacket when it cools down. So obsessed with this grungy-yet-romantic vibe!", "duration_ms": 2025, "stage_ms": {"search_listings": 226, "suggest_outfit": 1060, "create_fit_card": 738}, "wait_ms": 0, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 419, "output_tokens": 136, "model": "gemini-3.5-flash-lite", "timeout_s": 20.0, "fault": null}
{"ts": "2026-11-14T10:03:22.364+00:00", "run_id": "3eb78637", "query": "platform sneakers size 8", "parsed": {"description": "platform sneakers", "size": "8", "max_price": null}, "wardrobe_items": 10, "n_results": 1, "selected_id": "lst_019", "outcome": "ok", "error_type": null, "error_stage": null, "error": null, "fallbacks": [], "fit_card": "Chunky white platforms are officially my new daily uniform, especially since I managed to snag these gems on Poshmark for just $48. They're in such good condition and give me that exact 90s model-off-duty energy when I wear them with baggy denim. Can't wait to live in these all season long!", "duration_ms": 1671, "stage_ms": {"search_listings": 241, "suggest_outfit": 599, "create_fit_card": 831}, "wait_ms": 0, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 402, "output_tokens": 130, "model": "gemini-3.5-flash-lite", "timeout_s": 20.0, "fault": null}
{"ts": "2026-11-14T10:03:23.959+00:00", "run_id": "22020fdd", "query": "denim jacket under $50", "parsed": {"description": "denim jacket", "size": null, "max_price": 50.0}, "wardrobe_items": 10, "n_results": 7, "selected_id": "lst_007", "outcome": "ok", "error_type": null, "error_stage": null, "error": null, "fallbacks": [], "fit_card": "That perfect 90s light wash denim is finally mine. I scored this cropped beauty on Poshmark for just $42, and the quality is unreal. Can't wait to throw it on over a white tank and baggier jeans for the ultimate double-denim fit.", "duration_ms": 1593, "stage_ms": {"search_listings": 236, "suggest_outfit": 659, "create_fit_card": 698}, "wait_ms": 0, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 418, "output_tokens": 132, "model": "gemini-3.5-flash-lite", "timeout_s": 20.0, "fault": null}
{"ts": "2026-11-14T10:03:25.434+00:00", "run_id": "afd9f3a4", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "wardrobe_items": 10, "n_results": 10, "selected_id": "lst_002", "outcome": "ok", "error_type": null, "error_stage": null, "error": null, "fallbacks": [], "fit_card": "That buttery-soft fabric and nostalgic butterfly print are giving major 2000s pop princess energy. I manifested this exact Y2K baby tee for months before finally snagging it on Depop for just $18. Honestly obsessed with how it balances out with some oversized denim.", "duration_ms": 1474, "stage_ms": {"search_listings": 235, "suggest_outfit": 632, "create_fit_card": 606}, "wait_ms": 0, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 403, "output_tokens": 113, "model": "gemini-3.5-flash-lite", "timeout_s": 20.0, "fault": null}
{"ts": "2026-11-14T10:03:27.000+00:00", "run_id": "9ed396e7", "query": "90s track jacket in size M", "parsed": {"description": "90s track jacket", "size": "M", "max_price": null}, "wardrobe_items": 10, "n_results": 4, "selected_id": "lst_004", "outcome": "ok", "error_type": null, "error_stage": null, "error": null, "fallbacks": [], "fit_card": "That deep navy and white side-stripe on this 90s track jacket is just too good. Snagged it on Poshmark for $45 and it’s basically in brand-new condition. Honestly living for this sporty streetwear energy—gonna throw it on over a ribbed tank and baggy denim ASAP.", "duration_ms": 1565, "stage_ms": {"search_listings": 227, "suggest_outfit": 660, "create_fit_card": 678}, "wait_ms": 0, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 428, "output_tokens": 141, "model": "gemini-3.5-flash-lite", "timeout_s": 20.0, "fault": null}
{"ts": "2026-11-14T10:04:16.338+00:00", "run_id": "4b593a1d", "query": "silk slip dress in midi length under $40", "parsed": {"description": "silk slip dress midi length", "size": null, "max_price": 40.0}, "wardrobe_items": 10, "n_results": 5, "selected_id": "lst_013", "outcome": "ok", "error_type": null, "error_stage": null, "error": null, "fallbacks": [], "fit_card": "Ditsy florals and liquid silk scream peak 90s, and I couldn't resist adding this midi slip dress to my rotation. Snagged it on Depop for just $30, and it's in crazy good condition. I'm already planning to toughen it up with a white ribbed tank underneath and my chunky combat boots.", "duration_ms": 49336, "stage_ms": {"search_listings": 233, "suggest_outfit": 864, "create_fit_card": 48239}, "wait_ms": 47479, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 443, "output_tokens": 157, "model": "gemini-3.5-flash-lite", "timeout_s": 20.0, "fault": null}
{"ts": "2026-11-14T10:04:18.026+00:00", "run_id": "dbe75235", "query": "platform sneakers size 8", "parsed": {"description": "platform sneakers", "size": "8", "max_price": null}, "wardrobe_items": 10, "n_results": 1, "selected_id": "lst_019", "outcome": "ok", "error_type": null, "error_stage": null, "error": null, "fallbacks": [], "fit_card": "Crisp white chunky soles are officially doing all the heavy lifting this spring. Snagged these platform sneakers on Poshmark for just $48, and they’re honestly in such good shape. Paired with wide-leg khakis and a ribbed tank, they give off the best effortless 90s off-duty vibe.", "duration_ms": 1686, "stage_ms": {"search_listings": 228, "suggest_outfit": 684, "create_fit_card": 774}, "wait_ms": 151, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 408, "output_tokens": 134, "model": "gemini-3.5-flash-lite", "timeout_s": 20.0, "fault": null}
{"ts": "2026-11-14T10:04:19.748+00:00", "run_id": "83f919d0", "query": "denim jacket under $50", "parsed": {"description": "denim jacket", "size": null, "max_price": 50.0}, "wardrobe_items": 10, "n_results": 7, "selected_id": "lst_007", "outcome": "ok", "error_type": null, "error_stage": null, "error": null, "fallbacks": [], "fit_card": "That perfect 90s light wash denim is officially mine for just $42.00 after I hunted it down on Poshmark. I'm already planning to throw it over a ribbed white tank and wide-leg trousers for peak off-duty model energy. Trust me, you need a cropped jacket like this in your rotation ASAP.", "duration_ms": 1722, "stage_ms": {"search_listings": 236, "suggest_outfit": 698, "create_fit_card": 788}, "wait_ms": 0, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 431, "output_tokens": 156, "model": "gemini-3.5-flash-lite", "timeout_s": 20.0, "fault": null}
{"ts": "2026-11-14T10:04:29.779+00:00", "run_id": "695bfad9", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "wardrobe_items": 10, "n_results": 10, "selected_id": "lst_002", "outcome": "error", "error_type": "ModelTimeout", "error_stage": "suggest_outfit", "error": "The stylist model didn't answer within 0.01s while running suggest_outfit, so FitFindr stopped instead of leaving you waiting. Try again in a moment.", "fallbacks": [], "fit_card": null, "duration_ms": 704, "stage_ms": {"search_listings": 334, "suggest_outfit": 370}, "wait_ms": 0, "model_calls": 1, "cache_hits": 0, "prompt_tokens": 0, "output_tokens": 0, "model": "gemini-3.5-flash-lite", "timeout_s": 0.01, "fault": null}
{"ts": "2026-11-14T10:04:31.971+00:00", "run_id": "eec7817f", "query": "90s track jacket in size M", "parsed": {"description": "90s track jacket", "size": "M", "max_price": null}, "wardrobe_items": 10, "n_results": 4, "selected_id": "lst_004", "outcome": "ok_fallback", "error_type": null, "error_stage": null, "error": null, "fallbacks": ["suggest_outfit", "create_fit_card"], "fit_card": "90s Track Jacket — Navy/White Stripe, excellent condition — $45.00 on Poshmark. Thrifted, and ready to wear.", "duration_ms": 2076, "stage_ms": {"search_listings": 342, "suggest_outfit": 953, "create_fit_card": 781}, "wait_ms": 0, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 387, "output_tokens": 139, "model": "gemini-3.5-flash-lite", "timeout_s": 20.0, "fault": "empty"}
{"ts": "2026-11-14T10:04:35.688+00:00", "run_id": "1ace03f4", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "wardrobe_items": 10, "n_results": 10, "selected_id": "lst_002", "outcome": "error", "error_type": "RateLimited", "error_stage": "suggest_outfit", "error": "The model is rate-limiting this API key and kept refusing after 2 attempts during suggest_outfit. Wait a minute and ask again — your key is fine.", "fallbacks": [], "fit_card": null, "duration_ms": 3571, "stage_ms": {"search_listings": 335, "suggest_outfit": 3236}, "wait_ms": 3000, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 0, "output_tokens": 0, "model": "gemini-3.5-flash-lite", "timeout_s": 20.0, "fault": "ratelimit"}
{"ts": "2026-11-14T10:04:36.523+00:00", "run_id": "eed68c9f", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "wardrobe_items": 10, "n_results": 10, "selected_id": "lst_002", "outcome": "error", "error_type": "ModelUnavailable", "error_stage": "suggest_outfit", "error": "The model name 'no-such-model' did not resolve. If you changed AI201_MODEL in your .env, put it back. Otherwise post in the help channel — this is not something you caused.", "fallbacks": [], "fit_card": null, "duration_ms": 684, "stage_ms": {"search_listings": 338, "suggest_outfit": 346}, "wait_ms": 0, "model_calls": 1, "cache_hits": 0, "prompt_tokens": 0, "output_tokens": 0, "model": "no-such-model", "timeout_s": 20.0, "fault": null}
{"ts": "2026-11-14T10:04:36.982+00:00", "run_id": "009719fe", "query": "vintage graphic tee under $30", "parsed": {"description": "vintage graphic tee", "size": null, "max_price": 30.0}, "wardrobe_items": 10, "n_results": 10, "selected_id": "lst_002", "outcome": "error", "error_type": "QuotaGuard", "error_stage": "suggest_outfit", "error": "This session has used its request budget (0 model calls, SESSION_REQUEST_BUDGET in config.py), so FitFindr stopped before suggest_outfit. Restart to reset it.", "fallbacks": [], "fit_card": null, "duration_ms": 338, "stage_ms": {"search_listings": 338, "suggest_outfit": 0}, "wait_ms": 0, "model_calls": 0, "cache_hits": 0, "prompt_tokens": 0, "output_tokens": 0, "model": "gemini-3.5-flash-lite", "timeout_s": 20.0, "fault": null}
{"ts": "2026-11-14T10:04:37.391+00:00", "run_id": "630130d0", "query": "designer ballgown size XXS under $5", "parsed": {"description": "designer ballgown", "size": "XXS", "max_price": 5.0}, "wardrobe_items": 10, "n_results": 0, "selected_id": null, "outcome": "no_results", "error_type": null, "error_stage": null, "error": "No listings matched that description, size, and price. Try a plainer description, a higher max_price, or dropping the size.", "fallbacks": [], "fit_card": null, "duration_ms": 340, "stage_ms": {"search_listings": 340}, "wait_ms": 0, "model_calls": 0, "cache_hits": 0, "prompt_tokens": 0, "output_tokens": 0, "model": "gemini-3.5-flash-lite", "timeout_s": 20.0, "fault": null}
{"ts": "2026-11-14T10:04:39.862+00:00", "run_id": "1fe699a7", "query": "denim jacket under $50", "parsed": {"description": "denim jacket", "size": null, "max_price": 50.0}, "wardrobe_items": 0, "n_results": 7, "selected_id": "lst_007", "outcome": "ok", "error_type": null, "error_stage": null, "error": null, "fallbacks": [], "fit_card": "That perfect pale blue wash is notoriously hard to find, but Poshmark came through with this cropped denim jacket. At just $42, it’s already becoming my go-to layer for toughening up sweet floral midi dresses. Seriously obsessed with this effortless high-low mix!", "duration_ms": 2402, "stage_ms": {"search_listings": 344, "suggest_outfit": 973, "create_fit_card": 1085}, "wait_ms": 0, "model_calls": 2, "cache_hits": 0, "prompt_tokens": 281, "output_tokens": 122, "model": "gemini-3.5-flash-lite", "timeout_s": 20.0, "fault": null}
{"ts": "2026-11-14T10:04:40.510+00:00", "run_id": "58cb8fc4", "query": null, "outcome": "rejected", "error_type": "BadRequest", "error_stage": "serve", "error": "Send JSON with a 'query' field, e.g. {\"query\": \"vintage graphic tee under $30\"}", "http_status": 400, "body_bytes": 2, "duration_ms": 0, "model_calls": 0}
{"ts": "2026-11-14T10:04:40.517+00:00", "run_id": "83e4d733", "query": null, "outcome": "rejected", "error_type": "BadRequest", "error_stage": "serve", "error": "Send JSON with a 'query' field, e.g. {\"query\": \"vintage graphic tee under $30\"}", "http_status": 400, "body_bytes": 14, "duration_ms": 0, "model_calls": 0}
{"ts": "2026-11-14T10:04:40.523+00:00", "run_id": "5cef9dae", "query": null, "outcome": "rejected", "error_type": "BadRequest", "error_stage": "serve", "error": "Send JSON with a 'query' field, e.g. {\"query\": \"vintage graphic tee under $30\"}", "http_status": 400, "body_bytes": 5, "duration_ms": 0, "model_calls": 0}
{"ts": "2026-11-14T10:04:40.529+00:00", "run_id": "13af22b0", "query": null, "outcome": "rejected", "error_type": "BadRequest", "error_stage": "serve", "error": "Send JSON with a 'query' field, e.g. {\"query\": \"vintage graphic tee under $30\"}", "http_status": 400, "body_bytes": 8, "duration_ms": 0, "model_calls": 0}
```

**What It Costs**

Measured with `python measure_cost.py`: 10 full agent runs back to back,
cache off, across the 5 matching queries twice each, then averaged from the
run-log records those 10 runs wrote. The token counts are the service's own
`usage_metadata` numbers, summed per run in `generate.py::_record_tokens` (I
checked a raw response: this model reports no thinking tokens, so prompt +
output is the whole bill).

| Per run (average of 10) | |
|---|---|
| Model calls | 2.00 |
| Prompt tokens | 419.4 |
| Output tokens | 136.2 |
| Wall time | 6.49 s, of which 4.76 s was the rate limiter sleeping |
| Working time (wall minus waiting) | 1.73 s |
| **Dollars, paid tier** | **$0.000466** |

The dollar figure is the measured tokens times Google's published rate for
`gemini-3.5-flash-lite` (standard tier, $0.30 per 1M input and $2.50 per 1M
output, from ai.google.dev/gemini-api/docs/pricing, checked 2026-11-14):

    419.4 x $0.30 / 1,000,000  = $0.000126
    136.2 x $2.50 / 1,000,000  = $0.000341
                                 ---------
                       per run   $0.000466

On the free tier I actually run on, it costs $0.

A hundred people a day, one query each:

    100 runs x $0.000466 = $0.0466 a day,  x 30 = $1.40 a month

Money isn't the constraint at that scale — requests are. 100 runs is 200 model
calls, and the free tier allows 15 a minute, so a busy minute would be capped
at about 7 users and everyone after that waits. That's already visible in the
measurement: one of the 10 runs waited 47 seconds for a slot, which is why the
average wall time is 6.49 s when the work takes 1.73 s.

*Note after The Improvement below:* these numbers were measured before the
pacing change. The token-bucket limiter keeps the burst of 2 inside the same
15-a-minute allowance, so the steady rate is now 13 calls a minute — about
6.5 runs, not 7, in a busy minute. Tokens and dollars per run are unchanged;
the pacing only moves when calls go out, not what they cost.

**Run Log and Verdicts**

Produced by `python capstone_trials.py --label before --trial N`, N = 1, 2, 3,
run on 2026-11-15 after `criteria.md` was committed (`b5a69ee`), results
committed in `537a648`. Each run is 5 attempts per criterion; cache off;
how each attempt is scored is fixed in code at the top of
`capstone_trials.py`. Raw results: `results/capstone_before_trial{1,2,3}.json`,
log records: `logs/capstone_before.jsonl`.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Model timeout halts the run cleanly and is logged | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Empty model response triggers a logged fallback | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Malformed HTTP requests rejected without invoking the agent | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Telemetry accounts for rate-limiter waiting | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 5. Normal runs make exactly two model calls | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |

Real output, one attempt per criterion, from Run 1
(`results/capstone_before_trial1.json`):

Criterion 1 — `AI201_MODEL_TIMEOUT=0.01 python app.py ask '...'`; the record
written by `agent.py::run_agent` → `runlog.py::write`. Exit code 0, 1.2 s:

```json
{"run_id": "9e96075a", "query": "vintage graphic tee under $30", "outcome": "error", "error_type": "ModelTimeout", "error_stage": "suggest_outfit", "error": "The stylist model didn't answer within 0.01s while running suggest_outfit, so FitFindr stopped instead of leaving you waiting. Try again in a moment.", "fit_card": null, "duration_ms": 1029, "stage_ms": {"search_listings": 511, "suggest_outfit": 518}, "model_calls": 1, "timeout_s": 0.01}
```

Criterion 2 — `AI201_FAULT=empty`; fit card from `agent.py::_fit_card_fallback`,
record from `agent.py::run_agent`:

```json
{"query": "silk slip dress in midi length under $40", "fit_card": "90s Silk Slip Dress — Floral, Midi Length, good condition — $30.00 on Depop. Thrifted, and ready to wear.", "record": {"run_id": "91b3a32b", "outcome": "ok_fallback", "fallbacks": ["suggest_outfit", "create_fit_card"], "fault": "empty", "model_calls": 2}}
```

Criterion 3 — `POST /ask` with body `{"query": 123}`; response and record from
`serve.py::ask`. HTTP 400, no agent-run record appeared:

```json
{"run_id": "65af309d", "query": null, "outcome": "rejected", "error_type": "BadRequest", "error_stage": "serve", "error": "Send JSON with a 'query' field, e.g. {\"query\": \"vintage graphic tee under $30\"}", "http_status": 400, "body_bytes": 14, "duration_ms": 0, "model_calls": 0}
```

Criterion 4 — back-to-back runs; `wait_ms` from `generate.py::wait_seconds`,
`measured_sleep_ms` from the harness's own timer around `time.sleep`:

```json
{"query": "vintage graphic tee under $30", "measured_sleep_ms": 46323, "record": {"run_id": "5b189981", "duration_ms": 48562, "wait_ms": 46316, "stage_ms": {"search_listings": 235, "suggest_outfit": 46843, "create_fit_card": 1484}, "model_calls": 2}}
```

Criterion 5 — a normal query, record from `agent.py::run_agent`:

```json
{"run_id": "381b7df6", "outcome": "ok", "model_calls": 2, "prompt_tokens": 423, "output_tokens": 148, "duration_ms": 2387, "wait_ms": 0}
```

*All five MET — were the targets too low?* Partly, yes. Criteria 2 and 3 are
deterministic code paths with the fault switched on: an empty answer always
takes the fallback branch and a bad body always hits the 400, so 5/5 was close
to guaranteed unless I'd written a bug. Criterion 1 was the one I distrusted
most: `AI201_MODEL_TIMEOUT=0.01` fails at connection time (about 0.8 s), so it
never tested what the criterion is about — a model that takes the request and
then hangs. I tested that separately: pointed the client at a local socket
that accepts the connection and never replies, with a 3 s timeout. The run
stopped at 3.2 s with `ModelTimeout` in `suggest_outfit`. So criterion 1 holds
on a real stall too; it just didn't have to prove it.

The criterion I'd tighten is **1**, to add the time bound it was missing: *"When
the model accepts a request and then never answers, the run halts within
MODEL_TIMEOUT_S + 2 s and is logged as ModelTimeout — 5 of 5."* As written,
a run that hangs 19 s and then halts passes, and the reason I gave was about
hangs.

*What the run data showed that no criterion caught.* Criterion 4 was MET —
the wait was accounted for to within 10 ms every time — and the numbers it
accounted for were the most useful thing in the whole run. In 9 of 75 complete
runs the user waited more than 30 s, worst case 47.1 s (a 48.9 s run), while
the median run needed 1.9 s of work. The pasted criterion 4 record is one of
them: `suggest_outfit` took 46.8 s, of which 46.3 s was sleeping.

The stage is the rate limiter, `generate.py::_wait_for_slot`, and the
mechanism is that it's a 60-second sliding window with nothing in front of it:
it lets 15 calls straight through, then blocks the 16th until the oldest call
ages out of the window — about 46 s — so the waits come out bimodal, ~0 s or
~46 s, and the whole minute's debt lands on one unlucky run. It also sits
outside the hardening I built: the 20 s timeout covers the request, and this
sleep happens before the request is sent, so the "rescue the user from a hang"
reason behind criterion 1 doesn't reach it.

**The Improvement**

*What I changed:* a token bucket in front of the sliding window in
`generate.py::_wait_for_slot`, plus `PACING_BURST = 2` in `config.py`. Two
calls can go immediately — one whole agent run, for a user who's been idle —
and after that a token comes back every 60 / (15 − 2) = 4.6 s. Burst plus
refill can't exceed 15 calls in any 60 s window, so the old window check stays
as a backstop. Nothing else changed. Committed in `a167ff9`, before the after
runs.

*Why this one:* it follows the diagnosis above — the problem was where the
waiting landed, not how much of it there was, and spreading it is the direct
fix for "the whole minute's debt lands on one run".

Run log — After (`python capstone_trials.py --label after --trial N`, same
harness, same scoring; `results/capstone_after_trial{1,2,3}.json`,
`logs/capstone_after.jsonl`):

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Model timeout halts the run cleanly and is logged | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Empty model response triggers a logged fallback | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Malformed HTTP requests rejected without invoking the agent | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Telemetry accounts for rate-limiter waiting | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 5. Normal runs make exactly two model calls | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |

Side by side, from every complete run in the two trial logs (back-to-back
runs in one process, so the limiter is busy):

| | Before (75 runs) | After (45 runs) |
|---|---|---|
| Worst single run | 48.9 s | **9.8 s** |
| Worst limiter wait in one run | 47.1 s | **7.8 s** |
| Runs that waited > 30 s | 9 | **0** |
| Median run | **2.0 s** | 9.2 s |
| Mean run | **7.4 s** | 8.7 s |

Criterion 4 records after, one per run (`wait_ms` / measured sleep, ms):
`7698/7708, 7635/7645, 7313/7323, 7179/7189, 7278/7288` (Run 1).

*Did it help?* It did what it was aimed at, and it cost something. The worst
case went from 48.9 s to 9.8 s and no run waited more than 8 s, while all five
criteria stayed 5/5 — nothing I'd already hardened regressed. But under
sustained back-to-back load the typical run got slower: median 2.0 s → 9.2 s,
mean 7.4 s → 8.7 s. Before, most runs went free and a few paid for everyone;
now everyone pays a little, and slightly more in total because the steady rate
is 13 calls a minute instead of 15 (the burst of 2 comes out of the same 15).
For one user asking now and then, nothing changed: a run after an idle period
still waited 0 ms (checked with `app.py ask`, `wait_ms: 0`). I'd keep the
change — a predictable 9 s beats a 2 s that is sometimes 49 s — but it's a
trade, not a free win.

**What's Still Broken**

All five criteria were MET, before and after, so what's left is about where
the targets were soft and what the improvement cost.

- **Criterion 1 had no time bound.** I'd tighten it to "halts within
  MODEL_TIMEOUT_S + 2 s when the model accepts the request and never answers"
  and make the stalled-socket test part of `capstone_trials.py` instead of a
  one-off probe. I stopped because the one-off already passed (3.2 s against
  a 3 s timeout) and the unit's change budget went to the limiter.
- **Criteria 2 and 3 can't really fail.** They test my own branches with the
  fault forced on. A real empty response might be transient; the fallback
  takes over on the first empty answer without retrying once. I didn't add a
  retry because it would change criterion 5's call count, which is exactly the
  kind of interaction I'd want a criterion for first.
- **Steady-load throughput dropped from 15 to 13 calls a minute.** The fix
  traded average speed for worst-case speed. A burst of 1 would win back one
  call a minute but make every idle run wait 4.6 s for its second call.
- **The limiter wait still isn't covered by any timeout.** It's now bounded by
  the pacing (about 9 s worst case), not by a deadline. With more than one
  user, `serve.py` queues requests behind a lock, so a waiting request's real
  delay is the queue plus the pacing — neither shows in its own `wait_ms`.

*What I'd do next, if this were real:* put a whole-run deadline on `/ask` —
a budget covering queue time, pacing and the model call together, logged as
its own `error_type` — because the hardening this unit bounds each piece
separately and the user only ever experiences the sum. That's the first thing
that would fail with two users at once, and nothing measures it yet.

**How I Used AI**

1. *Choosing what to extend.* I gave Claude the capstone brief and asked which
   of my four projects would be least complex to extend. It assessed all four
   repos and ranked Provenance Guard first, because it already had structured
   logging. I asked it to compare just the Unofficial Guide and FitFindr, and
   picked FitFindr: I knew its failure modes best, and unit 4 had already
   shown me the model-call stage was its weak point. Claude then verified,
   by stubbing the model call, that `QuotaGuard` and the rate-limit
   `RuntimeError` really did escape `run_agent` before I wrote that into
   The Shape.
2. *Checking my criteria without letting it write them.* I wrote the five
   criteria and asked Claude to run each through the three self-check
   questions without rewriting them. It pointed out that criterion 1 had no
   time bound and that `generate.py` counts every retry attempt as a model
   call, which could put a 3 into criterion 5. I kept my wording as written
   and had the tests follow the assignment's 3-runs-of-5 format. The time-bound
   point is now my tightened criterion 1 above.

Claude also wrote the hardening code, the run log, the trial harness and the
cost script, and drafted these README sections from the committed results;
I directed each step and checked the numbers against the JSON results and
log files before committing.
