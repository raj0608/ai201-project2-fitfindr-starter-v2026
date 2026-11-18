# FitFindr — Demo Day notes

About 3 minutes, four parts. Read from this page; that's allowed.

---

## Before you present (5 minutes, do this first)

Open **two terminals** in the project folder, with `source .venv/bin/activate`
run in both.

```bash
python test.py          # must end with "10 passed"
```

Then do one practice question so the model is warmed up:

```bash
python app.py ask 'vintage graphic tee under $30'
```

Have these open in tabs: `criteria.md` (scroll to "Capstone criteria"), and
`README.md` (scroll to "Run Log and Verdicts").

---

## 1. What I built (about 45 seconds)

**Say:**

> "This is FitFindr. You tell it what secondhand item you want, like 'vintage
> graphic tee under thirty dollars'. It searches thrift listings, picks the
> best match, and then asks an AI model for two things: an outfit idea, and a
> short caption you could post about the find."

**Show** (terminal 1):

```bash
python app.py ask 'vintage graphic tee under $30'
```

> "It found an eighteen-dollar butterfly tee, suggested an outfit, and wrote a
> caption. That's two AI calls."

**Then say:**

> "For my capstone I didn't add a feature. I made it survive when the AI
> fails. Before, if the AI was slow, it could hang forever. If it sent back
> nothing, you got a blank caption. If you hit the rate limit, the program
> crashed. Now each of those ends with a clear message and a log entry."

**Show** one failure (terminal 1):

```bash
AI201_MODEL_TIMEOUT=0.01 python app.py ask 'denim jacket under $50'
```

> "Here I forced a timeout. Instead of hanging, it stops and tells the user
> why."

---

## 2. What standard I set (about 30 seconds)

**Read two criteria out loud, with the numbers:**

> "I wrote five pass/fail rules before testing anything. Two of them:
>
> **One:** if the AI times out, the run stops cleanly and is logged, 5 out of
> 5 times.
>
> **Four:** the logs keep track of time spent waiting on the rate limit
> separately from time spent on real work, 5 out of 5 times. Without that, you
> can't tell a slow AI apart from a traffic jam on my own side.
>
> I tested every rule 3 separate times, 5 attempts each."

---

## 3. What the test found (about 60 seconds) — the important part

**Say:**

> "All five rules passed, every time. Honestly, that told me some of my
> targets were too easy. Two of them test code paths where I turn the failure
> on myself, so they can't really fail.
>
> But the numbers from rule four showed a real problem. A normal run needs
> about **2 seconds** of actual work. But in **9 out of 75 runs**, the user
> waited **more than 30 seconds**. The worst one took **49 seconds**.
>
> The cause was my own rate limiter. The free AI plan allows 15 requests a
> minute. My limiter let 15 go through instantly, then made the next person
> wait almost a whole minute for a slot to open. So most runs were fast, and a
> few unlucky ones took all the waiting.
>
> And my timeout didn't catch it, because the waiting happens *before* the
> request is sent. So my 'no more hanging' fix had a hole in it."

**Optional, if there's time** (a second, smaller finding):

> "I also found one while rehearsing. On a Mac, my web server's port, 5000,
> is already taken by AirPlay, so every request came back 'Forbidden'. I moved
> it to port 8080."

---

## 4. What I changed (about 45 seconds)

**Say:**

> "I changed the limiter to spread requests out evenly instead of letting them
> all through at once and then stopping.
>
> Did it help? For the worst case, yes. The slowest run went from **49 seconds
> to under 10**, and no run waited more than 30 seconds. All five rules still
> passed.
>
> But it cost something. Under heavy use, a typical run went from **2 seconds
> to about 9**, because now everyone waits a little instead of a few people
> waiting a lot. A single user asking now and then doesn't notice any change.
>
> What's still broken: there's no time limit on the *whole* request, only on
> each piece. If I kept going, I'd add one overall deadline, because the user
> only feels the total."

---

## Numbers cheat sheet

| What | Number |
|---|---|
| AI calls per normal run | 2 |
| Real work per run | about 1.7–2 seconds |
| Cost per run (paid plan) | $0.000466, which is under a twentieth of a cent |
| 100 users a day | about $1.40 a month |
| Before the fix: runs waiting over 30 s | 9 of 75, worst 49 s |
| After the fix: worst run | 9.8 s, none over 30 s |
| After the fix: typical run under heavy use | 9.2 s (was 2.0 s) |
| Criteria passed | 5 of 5, in all 3 trials, before and after |

---

## If someone asks…

- **"Why not just raise the rate limit?"** It's the free plan's real limit of
  15 a minute. Going over it just gets errors from Google instead.
- **"How do you know the logs are right about waiting time?"** The test timed
  the waiting with its own separate stopwatch and compared. They matched
  within 10 milliseconds every time.
- **"Did you use AI?"** Yes, for writing scripts, finding errors, running the
  tests against my rules, and drafting the reports. I wrote the five rules
  myself.

---

## Peer testing — what to hand over

Give your partner the repo link. The **"Try it yourself"** and **"Sample
tests"** sections at the top of `README.md` are written for them. They will
need **their own Gemini API key** for the `.env` file.

Things they might hit:

- They forget single quotes, and `$30` disappears from the question.
- They're on a Mac and try port 5000 from an old habit. It's **8080**.
- A wardrobe in the wrong shape gives a messy error message (a known rough
  edge, listed in the README).

## Taking feedback — write it down here

Just listen, write it down, and ask one question. Don't explain or defend.

| | Notes |
|---|---|
| One thing that worked | |
| One thing that surprised them | |
| One thing they couldn't figure out | |
| My one question | |
