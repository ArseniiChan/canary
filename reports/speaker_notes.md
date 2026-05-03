# Canary — Speaker Notes for May 7 Presentation (v2)

**Length:** 6–7 minute slot, 7 slides.
**Realistic time budget:** target 6:30, hard ceiling 6:55. ("6:05" was fiction for a cold first run; building in real buffer.)
**Pacing rules:**
1. **No jargon out loud.** "Autoencoder", "MD&A", "rank-biserial", "truncated SVD", "MiniLM", "bottleneck", "out-of-sample" all stay on the slide and never leave your mouth.
2. **Don't pre-announce the conclusion.** Slide 1 sets the question; Slide 5 lands the punchline.
3. **Read numbers off the slide, not from memory.** All key numbers are visible — don't try to memorize them under pressure.
4. **The kill line is on Slide 5:** "the most decisive result in this study isn't the fancy method — it's that a method from before I was born matched it." Land that line clearly. Everything else supports it.

The speaker notes below are scripted to be **spoken**, not read. Every parenthetical is a stage direction, not something to say out loud.

---

## Slide 1 — Title    (target 0:25)

> "I'm Arsenii Chan. The question I built this project around is a simple one: **can a computer reading the words in a public company's annual report tell you which companies turned out to be committing accounting fraud?**
>
> Six famous cases. One specific test. Let me show you what came back."

*(Pause. Click to slide 2.)*

**Stage notes:** Don't announce your conclusion. Don't say "honestly" or "negative result" — both pre-spoil the talk. Open with the question; the audience leans forward.

---

## Slide 2 — Driving Question    (target 0:45)

> "Six historical fraud cases — Enron, WorldCom, Tyco, HealthSouth, Valeant, Lehman Brothers. Each one paired against companies in the same industry, same year, that turned out to be clean.
>
> The model never sees the word 'fraud' during training. It just learns what a typical annual report from that industry and year looks like, and flags filings that don't fit.
>
> The formal question is on the slide *(point at pull-quote)*. The one-line answer this report defends is on the next bullet *(point at it)*. I'll spend the rest of the talk on the evidence."

*(Click to slide 3.)*

**Stage notes:** Don't read the pull-quote out loud — it's full of jargon and the audience can read it faster than you can speak it. Just point. Same with the one-line answer.

---

## Slide 3 — The Lede: Methodological Contract    (target 0:50)

> "Before I show you any number, I want to put the methodology on the table — because the methodology is what makes the result mean anything.
>
> Three rules I locked in *before* I ran the test. (point at columns)
>
> **One — the model never sees a fraud during training.** For each fraud case, the model trains on clean filings from *other* cases. The fraud being tested is held out.
>
> **Two — the model never sees the future.** Within that training set, only filings dated on or before the fraud's filing date are eligible. The model can't be informed by language that came out *after* the fraud was discovered.
>
> **Three — single pass, no tuning.** Architecture, hyperparameters, the test set — all written down and locked into the repo *before* the test ran. *(point at the git-tag panel:)* Top right shows the actual lock — committed and tagged on May 1st, before any result came in.
>
> Test ran once. Whatever it said, that's the result."

*(Click to slide 4.)*

**Stage notes:** This is the most important slide. Slow down. The git-tag panel is small — say "top right shows" rather than gesturing at the podium. If anyone in the room knows what pre-registration is, this is where you've already won them over.

---

## Slide 4 — Per-fraud Results    (target 1:00)

> "Here's what came back. Five cases evaluable, one excluded — I'll come back to the excluded one.
>
> *(point at Lehman row)* Only Lehman lands in the top three within its peer group. Three out of thirteen. The statistical test is highly significant, *but* the effect size is small *(point at +0.12)*. Both numbers matter — reporting either one alone is misleading.
>
> *(quick scan with hand)* The other four — HealthSouth, Valeant, Tyco, WorldCom — all rank at or below random expectation. The test goes the *opposite* direction from what we'd want. Aggregate hit rates are at or below random.
>
> Now — Enron. *(point at italicized row)* Enron's filing date is April 2nd, 2001. Every other peer in every other case is dated later. Under the strict rule I locked in, Enron has no eligible training data.
>
> So I had a choice: relax the rule and rerun, or report the exclusion. I reported the exclusion. The pre-registered design was infeasible for the most famous case in the dataset, and I didn't catch that before I locked the spec — that's a finding about pre-registration, not about fraud detection."

*(Click to slide 5.)*

**Stage notes:** Hands ON the slide. Don't quote numbers from memory — point at them on the projection. The Enron exclusion is the most likely Q&A target; pre-empt it with "I had a choice — relax the rule or report the exclusion. I reported the exclusion."

---

## Slide 5 — Baseline Check    (target 1:10)

> "Now the part that I think actually matters.
>
> After the test ran, I asked myself the question every machine-learning paper should answer and most don't: **would a method from before I was born produce the same result?**
>
> So I ran one. *(point at chart left)* TF-IDF plus truncated SVD. It's the kind of thing you could have written in 1995 from a textbook. Same training data, same statistical tests, same pipeline shape. No neural network. No transformer.
>
> *(point at chart left)* On four of five cases, the 1995 method *ties* the modern one. *(point at Lehman bar)* On Lehman — the one case the modern method got — the 1995 method gets it *better*. *(point at chart right, Lehman bar)* By thirteen orders of magnitude on the statistical test.
>
> Let me say what I'm not saying and then what I am saying.
>
> *I am not saying* the modern method is broken, or that neural networks are unhelpful for this kind of problem.
>
> *I am saying* that on these five cases, with the rules I locked in, the modern method did not show a measurable advantage over a method I could have run in 1995.
>
> If you take one thing from this talk, this is it: **a sharp baseline isn't optional. A result that doesn't survive a baseline check isn't a result.**"

*(Click to slide 6.)*

**Stage notes:** This is the new lede. Don't rush. The "before I was born" / "1995" framing is the kill line — if it lands, the whole talk lands. Practice the deadpan delivery. If the room is silent after, that's fine — keep going. The "I am not saying / I am saying" structure prevents the misread "the AI didn't work."

---

## Slide 6 — Anticipated Questions    (target 0:40)

> "Three questions I expect — quick answers so we have time for whatever else you actually want to ask.
>
> *(speed)*
>
> **Why is Enron excluded — isn't that convenient?** No. The pre-registered rule produced an empty training set for the chronologically earliest fraud. I treat that as a design error, named in section 7 of the report, not a workaround.
>
> **Lehman has the largest training data of the four-times any other; is *that* the signal?** It's the obvious read. But Valeant has *more* training data than Lehman and ranks 8 out of 13. So the size confound doesn't hold up in our own data. The 1995 baseline shows the same Lehman result — which weakly argues for a real Lehman-specific signature, not a training artifact.
>
> **Could the embedding model have memorized 'Lehman' or 'Repo 105'?** I tested that. Masked 93 such mentions in Lehman's filing with a placeholder token, re-scored. Lehman's rank held. Literal-name leakage rejected.
>
> Other questions on the slide — happy to take them in Q&A."

*(Click to slide 7.)*

**Stage notes:** Cut from four questions to three (Executor advised). The fourth on the slide — about whether you ran a supervised classifier — gets handled in Q&A if it comes up. Don't try to deliver all four under pressure. The three on the slide are the ones the professor will most likely ask.

---

## Slide 7 — Three Lessons + URLs + Thanks    (target 0:45)

> "Three things this project taught me.
>
> *(point at 01)* **Pre-registration is load-bearing only if it survives contact with the data.** The contract held. I didn't iterate the model, I didn't redefine 'clean,' I didn't retreat from the Enron exclusion when the result was uncomfortable.
>
> *(point at 02)* **A sharp baseline is not optional.** This is the lesson the field needs more of. Most published methods don't run a 1995 baseline. This one did, and the 1995 baseline matched it.
>
> *(point at 03)* **A design error, owned, becomes a checklist.** Enron's exclusion is now a pre-flight check for the next iteration: enumerate exclusions before you freeze the contract, not after. And the next experiment is on the slide — same model, same filings, but compare the company against *itself* across years instead of against peers. That's the falsifiable next step this study couldn't run.
>
> Try it: *(point at slide footer)* `canary-psi.vercel.app/scan` — paste any 10-K, see how it scores against all five fraud cases. Code is on GitHub. Frozen-spec git tag is in the repo.
>
> Thanks. Happy to take questions."

*(End. Open Q&A.)*

**Stage notes:** Land the URLs cleanly. Pause for one beat after "Thanks." Don't run into the next sentence. If you've delivered slides 1-7 cleanly, your face should look calm. Look up at the audience for the URL line — that's the call-to-action.

---

## Time budget — at a glance

| Slide | Topic | Target | Cumulative |
|---|---|---:|---:|
| 1 | Title + question | 0:25 | 0:25 |
| 2 | Driving question + one-line answer | 0:45 | 1:10 |
| 3 | Methodological contract | 0:50 | 2:00 |
| 4 | Per-fraud results | 1:00 | 3:00 |
| 5 | Baseline check (the lede) | 1:10 | 4:10 |
| 6 | Anticipated questions | 0:40 | 4:50 |
| 7 | Three lessons + URLs | 0:45 | 5:35 |
| **Total target** | | | **5:35** |

That gives you 1:25 of buffer for transitions, slow start, panel laughter, and the natural inflation of a cold first run. **If a rehearsal hits 7:30+, the cuts are:**
- Drop the "I am not saying / I am saying" structure on Slide 5 (saves ~15s)
- Skip the Valeant counter-confound on Slide 6 (saves ~15s)
- Skip the within-firm-change-detection callout on Slide 7 (saves ~10s)

**Total possible cuts: ~40s. Don't cut more — those are scripts you've memorized for a reason.**

---

## Rehearsal schedule (Mon May 4 — Thu May 7)

- **Sun May 3 evening:** Full run with phone timer. Record audio. Don't edit notes yet — just listen back.
- **Mon May 4:** Listen to Sunday's recording. Edit notes where you stumbled. Two short runs in the afternoon, focused on the ROUGH spots, not full talks.
- **Tue May 5 evening:** Two full runs. The second one out loud to a human friend, parent, or roommate. Ask: "After hearing that, what do you think this project did?" Their answer tells you what's landing.
- **Wed May 6 afternoon:** One full run in the actual presentation room if the building is open. One full run that evening, timed.
- **Thu May 7 morning:** Light walk-through ONLY. No full runs. No edits. The talk is whatever you're going to deliver — don't introduce new material 2 hours before.

---

## Q&A cheat sheet — three prepared answers

The three highest-probability hostile questions. Practice these out loud at least twice before May 7 — they should sound natural, not memorized.

> **"Why didn't you compare against a supervised classifier — logistic regression on labels, for instance?"**
>
> "The pre-registered design avoided supervised training because at six fraud examples a supervised classifier overfits trivially. A supervised baseline is genuinely good future work. For this study it would have violated the contract."

> **"Doesn't a tiny p-value with a small effect size just tell us the test is sensitive to sentence count?"**
>
> "Yes — that's exactly why I report effect size alongside the p-value. The p-value scales with how many sentences you have; the effect size doesn't. That's why both numbers are on the slide."

> **"How can you trust the parser at 93.6% extraction success? What about the 6.4% that failed?"**
>
> "The five failures are all in pre-2001-vintage peer filings. Every fraud parsed at 100%. I report the per-cohort breakdown in the parsing-QA appendix. No manual fixes were applied, so there's no asymmetric correction risk."

If you don't know an answer in Q&A, the right line is: **"That's a real gap I haven't characterized — let me follow up after the talk."** Don't fake numbers under pressure. Saying "I don't know" is graduate-school behavior, not undergrad weakness.

---

## Three things to memorize, three things to read off the slide

**Memorize (rehearse until automatic):**
1. The opening question on Slide 1.
2. The "I am not saying / I am saying" structure on Slide 5.
3. The "a sharp baseline is not optional" line on Slide 7.

**Read off the slide (do NOT memorize):**
1. The numbers on Slide 4 (3/13, 7/12, 8/13, 9/13, 12/13, p-values, effect sizes).
2. The full pull-quote on Slide 2.
3. The git-tag-and-commit-hash on Slide 3.

**Why split this way:** the lines you memorize are the *frame* — they shape how the audience receives the numbers. The numbers themselves are just evidence; the slide can hold them. Don't burn rehearsal time memorizing what the projector will show.
