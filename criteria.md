# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
`search_listings` scores matches by plain keyword overlap between the parsed
description and each listing's title/description/tags — there's no synonym
handling, so a phrasing that doesn't share a word with the listing text (e.g.
"tee" when the listing only says "shirt") can legitimately score zero even
though a human would call it a match. 4 of 5 leaves room for that class of
miss without excusing an actual bug, which 3 of 5 or lower would start to do.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
Unlike criterion 1, this path doesn't depend on the model guessing right or
the keyword scorer being generous — it's an `if not results:` branch in my
own code, checked the same way every time. Nothing here is allowed to vary
run to run, so anything short of 5 of 5 would mean the branch itself is
broken, not that the task was hard.

---

## 3. Something about state

For a matching query, the `id` of `session["selected_item"]` recorded right
after `search_listings` returns is identical to the `id` of the `new_item`
dict that `suggest_outfit` is actually called with — checked by printing both
ids — in 5 of 5 tries.

**Why this target:**
This is a plain dict assignment and a function argument, not model output —
nothing about it is supposed to vary from run to run. If the id ever
mismatched, that would mean the session was overwritten or a stale variable
was passed around it instead of through it, which is a real bug, not noise. A
target below 5 of 5 would be hiding that bug behind an acceptable failure
rate.

---

## 4. Something about the fit card

Across 5 runs on 5 different items, every fit card mentions that item's exact
price (e.g. "$24.00" or "24") at least once — 5 of 5 tries — and no two of the
five cards share the same opening sentence.

**Why this target:**
The price is data I hand the model in the prompt, not something it has to
invent, so there's no reason it should ever get dropped — 5 of 5 is fair.
The opening-sentence check is the part that has to tolerate the model: at
TEMPERATURE 0.9 I expect genuinely different wording for different items, but
I'd be unhappy if the model fell back to one template. Uniqueness across only
5 samples is a low bar for "isn't a template," not a claim that it never
repeats at any scale.

---

## 5. Your choice

Given a `max_price`, every listing `search_listings` returns has
`price <= max_price`, checked across 5 different queries with 5 different
price ceilings — 5 of 5 tries.

**Why this target:**
Price filtering is a numeric comparison in my own code with no model in the
loop, so there's no source of legitimate variation — a ceiling that lets
through one overpriced item isn't bad luck, it's an off-by-one or a skipped
filter. This is the criterion I'd trust least if I set it below 5 of 5,
because a miss here means the tool is lying about what it filtered, not that
the data was ambiguous.



---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
