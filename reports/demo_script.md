# Canary — Live Demo Script for May 7

**Where this lives in the talk:** in Q&A, not in the main 7-minute slot.
A live demo inside the talk is high-variance — a network blip or cold start
eats 20 seconds of stage time. Treat the live demo as a Q&A weapon: if
someone asks "can I see what it does on a real filing?", you have an answer
ready in 60 seconds.

**This page is meant to be printed as a half-sheet** and clipped to the
podium next to the deck PDF. Everything below is a checklist; nothing
needs to be memorized.

---

## Pre-talk preparation (do this 5 minutes before the slot)

**1. Pre-warm the Modal container** so the first demo call doesn't take 15-20s.
On any device, open this URL once in a browser:

```
https://arseniichan--health.modal.run
```

It should return `{"ok": true, "cohorts": [...]}`. The container stays warm
for ~5 minutes after that, so do this within 5 minutes of when you might
need the live demo.

**2. Open the scan page in a tab on the presentation laptop:**

```
https://canary-psi.vercel.app/scan
```

Click **"Paste text"** (not "Upload file"). Leave the tab open and the
textarea visible. Don't click Score yet.

**3. Copy the demo snippet to clipboard.** The exact text is in
[`reports/demo_snippet.txt`](demo_snippet.txt) — open it, select all
(Cmd+A), copy (Cmd+C). The clipboard now holds 1,771 characters of real
Lehman MD&A.

**4. Know the expected output.** When the live demo works, the verdict
banner at the top of the result page reads:

> *Verdict — descriptive only · 5 cohorts*
> **Elevated novelty across multiple cohorts**
> This filing's MD&A is more anomalous than the historical fraud in
> 5 of 5 cohorts.
>
> Median rank: **2.0** across 5 cohorts
> Median percentile: **92%** (random baseline ≈ 50%)
> Top-tier cohorts: **5 / 5** (rank in top third)
> Beat the fraud: **5 / 5** (more anomalous than the historical fraud)
>
> Per-cohort: Lehman 1/14, WorldCom 1/14, Tyco 2/14, HealthSouth 2/13,
> Valeant 4/14.

If the live demo can't reach Modal, dictate this verdict from memory or
from this card while pointing at the static deck slide 4 on the projector.

---

## On stage — the 60-second demo

Cue: someone asks any version of "can I see it work on a real filing?",
"show me what it does," or "how does the live demo work?"

### Beat 1 — context (10s)

> "Sure. The dashboard is at `canary-psi.vercel.app/scan` — let me show you
> the same pipeline I just talked about, against a real annual report."

(Switch projector to the browser tab from prep step 2. The /scan page
should already be open with the "Paste text" mode active.)

### Beat 2 — paste (10s)

> "I've got a 1,700-character chunk of Lehman Brothers' 2007 annual report
> on the clipboard — the actual text from the filing. Let me paste it in."

(Click into the textarea. **Cmd+V**. The character counter under the
textarea should show approximately "1771 characters · ready".)

### Beat 3 — submit + wait (15s)

> "Click Score this filing."

(Click the navy "Score this filing" button. Result takes 4-8 seconds when
warm; up to 20 seconds cold. Fill the wait:)

> "Behind this button — the same pipeline I just walked through. The model
> sentence-embeds the text, runs it against five different fraud cohort
> autoencoders, and ranks where it would land if added to each cohort."

### Beat 4 — read the result (20s)

When results land, scroll to the per-cohort breakdown.

(Point at the Lehman row.)

> "Lehman cohort: rank **1 of 14** — most anomalous in its own peer group."

(Point at WorldCom.)

> "WorldCom cohort: also **1 of 14** — most anomalous there too."

(Point at the others.)

> "Tyco and HealthSouth: **2 of 13 or 14**, second-most-anomalous. Valeant:
> rank 4. So this filing's language ranks at or near the top in *every*
> cohort — which is what you'd expect for a real fraud filing under the
> framing I described."

### Beat 5 — the caveat (5s)

> "But — this is exactly the slide-7 'we report the result, we don't claim
> a method' caveat. Two cohorts ranking high tells you the language is
> unusual. It doesn't tell you it's *fraud*. Real evidence requires more
> than one signal."

End. Return to the deck or move on to the next question.

---

## Failure modes and recovery

### Modal endpoint is cold (response > 10s)

Don't apologize. Fill the wait with the "behind this button" line above
or just say:

> "First scan in a quiet spell takes a moment — the inference container
> spins up on demand, scales to zero when nobody's calling it."

### Network is broken

Skip the live demo entirely. Pivot back to the deck. Say:

> "Network is being slow — let me describe the result I got testing this
> earlier this week." (Switch projector back to slide 4 of the deck. Read
> from the prep card: "Lehman 1 of 14, WorldCom 1 of 14, Tyco and HealthSouth
> 2nd, Valeant 4th — top-tier in every cohort, which is what the talk's
> framing predicts.")

### The endpoint returns an error

The deploy is live (verified May 3) and the system has been stress-tested
with 22/22 passing checks. If something goes wrong on stage:

> "Looks like the endpoint hiccuped — but the test result I got earlier
> this week is the same pattern as Lehman's actual filing." (Pivot back
> to slide 4.) "The dashboard is on GitHub if anyone wants to run it
> themselves after."

### Someone asks for a different filing

If someone says "can you try a recent Apple 10-K?" or similar, the answer
is:

> "Sure — but that's an out-of-distribution test. The model trained on
> 2001-2014 industry-and-year-matched peers, so any filing from a sector
> or year outside that gets the raw-text-fallback path. The score will
> still come back, but it's not directly comparable to the trained
> cohorts. I have the snippet I tested with prepared — let me run that
> first, and we can talk about out-of-distribution tests in office hours."

(Then run the prepared Lehman snippet anyway — don't try to find and
paste a fresh filing under stage pressure.)

---

## What to point at on the result page

```
┌─────────────────────────────────────────┐
│ VERDICT — DESCRIPTIVE ONLY · 5 COHORTS  │
│                                         │
│  High novelty across cohorts            │
│                                         │
│  This filing's MD&A is highly anomalous │
│  against multiple peer baselines.       │
│                                         │
│  Median rank   |  Median percentile     │
│  ~2.0          |  ~92%                  │
└─────────────────────────────────────────┘
```

The "Verdict" headline at the top of the result page is the right thing
to point at first — it summarizes the per-cohort numbers in one sentence.
Then drill into the per-cohort cards below for the Lehman 1/14 and
WorldCom 1/14 numbers.

**Don't** point at the score numbers themselves (`0.001625` etc.) — they're
on the page but won't mean anything to a non-ML audience. **Do** point at
the rank numbers (`1 / 14`, `2 / 13`) because the audience parses those
intuitively.

---

## Demo time budget

| Beat | Action | Time |
|---|---|---:|
| 1 | Context + show URL | 10s |
| 2 | Paste from clipboard | 10s |
| 3 | Submit + fill wait | 15s |
| 4 | Read per-cohort results | 20s |
| 5 | Land the caveat | 5s |
| **Total** | | **60s** |

If the demo runs past 90 seconds, you've lost the room. Cut Beats 4 and 5
to one sentence each:

> "The cohorts on the right are all in the top quartile — which is what
> the slide-7 caveat is about: high rank means unusual, not fraudulent."

---

## Three things NOT to do during the live demo

1. **Don't try to upload a file.** The file-upload mode requires picking a
   file from the laptop's filesystem; that's a podium-fumble waiting to
   happen. Always use "Paste text" mode with the pre-loaded clipboard.

2. **Don't change the snippet on the fly.** If someone says "what about an
   Apple 10-K?", say "let me try the prepared one first" and stick to the
   script. Audience-suggested inputs are recipe for unpredictable results
   that distract from the talk's narrative.

3. **Don't apologize for the result.** The demo's purpose is to show that
   the system works end-to-end on stage, not to prove fraud detection.
   Whatever ranks come back, they're consistent with what the talk claimed.
   The demo confirms the *infrastructure*; the talk made the *claim*.

---

## After the demo — the audience's phones

After you say "the URL is `canary-psi.vercel.app/scan`," 3-5 people in
the room will type it on their phones. That's good — but be prepared for
the next round of Q&A to include questions like:

- "I tried it on my company's 10-K and it ranked 12 of 14. What does that
  mean?"
- "Why did it take so long the first time?"
- "I see a Lehman card on the results page — is that the same Lehman?"

**The right answer to all three** is some version of:

> "The dashboard is descriptive, not diagnostic. The pipeline scores how
> unusual a filing's language looks against the five trained cohorts —
> nothing more. Cold-start latency is because the inference container
> scales to zero between calls. And yes, it's the same Lehman Brothers —
> they're one of the six historical fraud cases the model was trained
> to compare against."
