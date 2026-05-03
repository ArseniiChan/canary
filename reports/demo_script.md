# Canary — Live Demo Script for May 7  (v2 — council-revised)

**Where this lives in the talk:** in Q&A, not in the main 7-minute slot.

**Prior council-pass verdict:** v1 of this script accidentally argued
*against* the talk's thesis — by demoing with a Lehman snippet that
contained the literal string "LEHMAN BROTHERS HOLDINGS INC.", v1 invited
the read "your model just read the company name." v2 fixes that with a
single change: **the demo snippet no longer contains the word "Lehman"
anywhere.** The result holds (verified end-to-end on the live endpoint —
identical six-decimal scores with and without the company name). The
demo's lede is now the entity-masking ablation made live: "I removed
every mention of 'Lehman' and it still ranks first in 5 of 5 cohorts."

This page is meant to be **printed as a half-sheet** and clipped to the
podium next to the deck PDF. Nothing below needs to be memorized.

---

## Pre-talk preparation (do these in order)

### Wednesday May 6 evening — infrastructure hardening

**1. Decide on Modal `min_containers`.** The demo fires reactively in
Q&A, after a 7-minute talk. By the time anyone asks, Modal has been
cold for 12+ minutes, and the first call takes 15-25s of dead air. Two
options:
- *(recommended for Thursday only)*: edit `serve/modal_app.py`, change
  `min_containers=0` to `min_containers=1`, redeploy with
  `python -m modal deploy serve/modal_app.py`. One container stays
  warm. Costs ~$0.10–0.30/hr while it's up. Revert Friday morning.
- *(zero-cost fallback)*: a confederate in the audience taps
  `https://arseniichan--health.modal.run` on their phone the moment
  you say "I can show you live" — the demo trigger phrase. Container
  warms in ~5 seconds while you're still talking.

**2. Pre-fill the textarea via URL parameter.** v2 adds a URL-param path
so the snippet loads without needing clipboard access (which a managed
Windows podium PC may block). Test the URL the night before from a
phone:

```
https://canary-psi.vercel.app/scan?demo=1
```

If that works, you don't need to paste anything on stage — the textarea
arrives pre-filled. (If `?demo=1` isn't yet shipped, fall back to the
clipboard plan below.)

**3. Bring three copies, two formats, three independent paths.**
- Personal laptop with everything pre-warmed
- Thumb drive containing `reports/demo_snippet.txt` and the deck PDF
- Phone hotspot, tested in airplane mode failover
- The deck PDF open in **Preview** (not Chrome) so a Chrome crash
  doesn't kill recovery

### Thursday May 7 — minutes before the slot

**1. Warm Modal.** Hit `https://arseniichan--health.modal.run` once on
your phone within 5 minutes of walking up. Should return
`{"ok":true,"cohorts":[...]}`. If `min_containers=1` is on, this is
unnecessary but harmless.

**2. Open `canary-psi.vercel.app/scan` in a tab on the presentation
laptop.** Click **"Paste text"**. If the URL-param path is shipped, use
`canary-psi.vercel.app/scan?demo=1` so the textarea pre-fills. Don't
click Score yet.

**3. Have the deck open in Preview** — separate app window, ready for
Cmd+Tab back if the demo fails.

**4. Know the expected output.** When the live demo works, the verdict
banner reads:

> *Verdict — descriptive only · 5 cohorts*
> **Elevated novelty across multiple cohorts**
> This filing's MD&A is more anomalous than the historical fraud in
> 5 of 5 cohorts.
>
> Median rank: **2.0** across 5 cohorts
> Median percentile: **92%** (random baseline ≈ 50%)
> Top-tier cohorts: **5 / 5**
> Beat the fraud: **5 / 5**
>
> Per-cohort: LEH 1/14, WCOM 1/14, TYC 2/14, HRC 2/13, VRX 4/14.

If the live demo can't reach Modal, dictate this verdict from this
card while pointing at the static deck slide 4.

---

## On stage — the 60-second demo  (REWRITTEN per council)

Cue: someone asks any version of "can I see it on a real filing?" or
"how does the live demo work?"

### Beat 1 — context (10s)

> "Sure. The dashboard is at `canary-psi.vercel.app/scan` — same pipeline
> I just talked through, against a real annual report."

(Switch projector to the browser tab. Scan page should already be open
with the textarea pre-filled.)

### Beat 2 — the framing (15s)  ← REWRITTEN

> "I'm pasting a chunk of Lehman's 2007 annual report — but with one
> change: **I removed every mention of the word 'Lehman' from the
> input first**. So whatever ranks come back, the model isn't matching
> a literal name. It's responding to the language pattern. This is the
> live counterpart of the entity-masking ablation in section 7 of the
> report."

(If using clipboard path, paste now. If pre-filled via URL param,
just point at the textarea: "the snippet's already in there.")

### Beat 3 — submit + wait (10s)

> "Click Score this filing. Behind this button — sentence embeddings,
> five different cohort-specific autoencoders, mean per-sentence
> reconstruction error against each."

(Click the navy "Score this filing" button. Result takes ~5s warm,
up to 20s cold.)

### Beat 4 — read results, with the right framing (20s)  ← REWRITTEN

When results land, scroll to the verdict banner.

> "Verdict says elevated novelty across 5 of 5 cohorts. Even with the
> name removed from the input, the model lands the snippet at rank 1
> in two cohorts — its own (Lehman) and WorldCom. That second one is
> the interesting result: the language reads as anomalous in a
> different industry's cohort too. Tyco and HealthSouth, second-most.
> Valeant, fourth.
>
> So the signal isn't literal-name leakage — that's what the report's
> section 7 ablation showed offline, and this is the live version of
> it."

### Beat 5 — the caveat (5s)  ← REWRITTEN

> "But — slide 7 caveat applies. High rank means the language is
> linguistically unusual. It does not say it's fraud. The talk's
> baseline finding still holds: a 1995 method does this just as well."

End. Return to the deck or move on.

---

## Why v2 doesn't contradict the talk

The council found that v1's framing accidentally argued *for* the
autoencoder being a working detector — exactly the claim the talk's
slide 5 explicitly disowns. v2 fixes that with three reframes:

1. **The demo's lede is the entity-masking ablation, not the per-cohort
   ranks.** The interesting fact is that the result holds without
   "Lehman" in the input. That defends a *methodological* claim
   (the signal isn't name-leakage), which is consistent with the
   talk's epistemics.

2. **Beat 4 explicitly names the WorldCom rank as "the interesting
   result"** — i.e., the part that's not yet explained, not the part
   that confirms expectation. That keeps the talk's "we report the
   result, we don't claim a method" stance intact.

3. **Beat 5 explicitly returns to the baseline finding** — "a 1995
   method does this just as well." The demo doesn't escape from
   slide 5's verdict; it lives inside it.

If a Q&A questioner says "isn't this just confirmation bias — pick the
cohort that worked, paste its own text?", you have a real answer:

> "Fair question. Two reasons it's not. First, I removed the company
> name from the input — the result you just saw doesn't depend on the
> literal token 'Lehman'. Second, the talk's whole point is that the
> autoencoder did NOT show a measurable advantage over a 1995 baseline
> on this signal. The demo is consistent with that — it shows the
> infrastructure works, not that the autoencoder is a working
> detector. Slide 5 is still the headline."

---

## Failure modes and recovery

### Modal endpoint is cold (response > 10s)

Don't apologize. Fill the wait:

> "First scan in a quiet spell takes a moment — the inference container
> spins up on demand and scales to zero when nobody's calling it. That
> latency you're watching is real cold-start, which is what production
> systems trade for cheap inference."

### Network is broken

Skip the live demo entirely. Cmd+Tab back to the deck (open in Preview,
not Chrome). Say:

> "Network's slow — let me describe the result I got testing this
> earlier this week." (Switch projector back to slide 4. Read from
> the prep card: "LEH 1/14, WCOM 1/14, TYC and HRC 2nd, VRX 4th —
> with the name removed from the input.")

### The endpoint returns an error

> "Endpoint hiccupped — but the result I got testing earlier this
> week is the same pattern as the entity-masking ablation in
> section 7 of the report." (Pivot to deck.) "The dashboard is on
> GitHub if anyone wants to run it themselves."

### Chrome crashes

Cmd+Tab to Preview (deck). Don't try to recover Chrome. Live demo's
over; rest of the Q&A continues from the deck.

---

## What to point at on the result page

The verdict banner at the top is the right thing to point at first:

```
VERDICT — DESCRIPTIVE ONLY · 5 COHORTS
Elevated novelty across multiple cohorts
This filing's MD&A is more anomalous than the historical fraud in 5 of 5 cohorts.

Median rank   |  Median percentile  |  Top-tier cohorts  |  Beat the fraud
2.0           |  92%                |  5 / 5             |  5 / 5
```

Don't point at the score numbers (`0.001625` etc.) — they're invisible
to a non-ML audience. Point at the rank fractions (`1 / 14`, `2 / 13`)
because those parse intuitively.

---

## Demo time budget (v2)

| Beat | Action | Time |
|---|---|---:|
| 1 | Context + URL | 10s |
| 2 | Framing — name removed from input | 15s |
| 3 | Submit + fill wait | 10s |
| 4 | Read results, name "interesting" result | 20s |
| 5 | Caveat — return to slide 5 baseline finding | 5s |
| **Total** | | **60s** |

If the demo runs past 90s, cut Beat 2 to one sentence ("I removed every
'Lehman' from the input") and Beat 4 to two ("rank 1 in two cohorts;
WorldCom is the interesting one"). Don't cut Beat 5 — that's the line
that prevents the misread.

---

## Three things NOT to do during the live demo

1. **Don't try to upload a file.** File-upload mode requires picking a
   file from the laptop's filesystem; that's a podium-fumble waiting
   to happen. Always use "Paste text" mode with pre-loaded clipboard
   or the URL-param path.

2. **Don't change the snippet on the fly.** If someone says "what
   about an Apple 10-K?", say "let me run the prepared one first" and
   stick to the script. Audience-suggested inputs are recipe for
   unpredictable results that distract from the talk's narrative.

3. **Don't apologize for the result, but don't oversell it either.**
   The demo's purpose is to show that the system works end-to-end on
   stage AND to demonstrate the entity-masking ablation live — not to
   prove fraud detection. The talk's slide 5 baseline finding is the
   thesis; the demo is consistent with it.

---

## After the demo — phone-screen Q&A

After you say "the URL is `canary-psi.vercel.app/scan`," 3-5 audience
members will type it on their phones. Be ready for follow-ups:

- **"I tried it on my company's 10-K and it ranked 12 of 14. What does
  that mean?"** Answer: "It means the language ranks as more typical
  of a clean filing than of one of those five fraud cases — which is
  what we'd expect for a real clean filing. It does *not* mean
  anything is wrong with your company. The dashboard is descriptive,
  not diagnostic."

- **"Why did it take so long the first time?"** Answer: "Cold start.
  The inference container scales to zero between calls and respins
  when needed. After your first call, subsequent calls are sub-second."

- **"I see a Lehman card on the results page — is that the same
  Lehman?"** Answer: "Yes. Lehman Brothers' 2007 10-K is one of the
  six historical fraud cases the model was trained to compare against."

- **"Is this a fraud detector?"** Answer: **"No. The talk's slide 5
  found that a 1995 baseline method does this just as well as the
  neural model. Treat the dashboard as a research artifact, not a
  detector."** (Land this one cleanly. It's the most important
  question in this section.)

---

## Or — should the demo happen at all?

A serious case can be made to **cut the demo entirely.** The argument:
a working dashboard URL on slide 7 does the same job at zero risk and
zero contradiction cost. Live demos exist to prove something a
screenshot can't, and here nothing qualifies.

I'm keeping the demo because (a) the entity-masking framing of v2
genuinely demonstrates something the screenshot can't (the result is
invariant under name removal — that's a *finding*, not a button press),
and (b) the demo gives the audience something to type into their
phones, which generates exactly the post-talk engagement an undergrad
project benefits from.

But: **if Wednesday's full rehearsal hits any technical hiccup with
the live demo path** — Chrome crashes, Modal timeouts, projector
oddness — **cut it on Thursday morning** and replace the Q&A response
with: "The dashboard is at `canary-psi.vercel.app/scan` — try it after.
Section 7 of the report walks through the entity-masking ablation in
detail." That's the safe answer if the live path can't be trusted.
