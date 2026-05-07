#!/usr/bin/env node
/* eslint-disable */
// Build canary deck (7 slides) ordering:
//   1. Title
//   2. Driving question (pull quote)
//   3. The methodological contract
//   4. Per-fraud results: Lehman, others, Enron exclusion in one frame
//   5. The trivial baseline matched or exceeded the autoencoder
//   6. Questions I expect (Q&A defense)
//   7. Conclusion, next experiment, repo, thanks
//
// 13.33" × 7.5" widescreen. Run with NODE_PATH=$(npm root -g).

const path = require("path");
const PptxGenJS = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const FIG = (n) => path.join(ROOT, "reports/figures", n);
const OUT = path.join(ROOT, "reports/canary_deck.pptx");

const pres = new PptxGenJS();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.title = "Canary: Pre-Registered Single-Signal Novelty Study on SEC 10-K MD&A";
pres.author = "Arsenii Chan";
pres.company = "CSC 44800, CCNY, Spring 2026";

// Palette: black + electric blue accent (taken from Canva template slide 1)
const NAVY = "1A2B4C";
const NAVY_DARK = "141519";    // template background near-black
const NAVY_LIGHT = "5B7BB0";
const CANARY = "3B82F6";       // electric blue accent (brightened from template's #0A279F for legibility on dark backgrounds)
const INK = "1A1A1A";
const INK_2 = "555555";
const INK_3 = "8A8A8A";
const RULE = "D9D9D9";
const SURFACE = "F8F8F4";       // warm near-white for cards
const SURFACE_2 = "FFFFFF";

const SERIF = "Georgia";
const SANS = "Calibri";

// ---------- Slide helpers ----------
function pageFooter(slide, n, total) {
  slide.addText(`Canary  ·  Arsenii Chan  ·  CSC 44800`, {
    x: 0.5, y: 7.05, w: 8, h: 0.3,
    fontFace: SANS, fontSize: 10, color: INK_3, align: "left",
  });
  slide.addText(`${n} / ${total}`, {
    x: 11.83, y: 7.05, w: 1, h: 0.3,
    fontFace: SANS, fontSize: 10, color: INK_3, align: "right",
  });
}

function eyebrow(slide, x, y, text) {
  slide.addText(text, {
    x, y, w: 12, h: 0.3,
    fontFace: SANS, fontSize: 11, bold: true, color: NAVY_LIGHT,
    charSpacing: 4, // letter spacing
  });
}

function rule(slide, x, y, w, color = CANARY, h = 0.04) {
  slide.addShape(pres.ShapeType.rect, { x, y, w, h, fill: { color }, line: { color, width: 0 } });
}

// ---------- Slide 1: Title ----------
const s1 = pres.addSlide();
s1.background = { color: NAVY_DARK };
s1.addText("CANARY", {
  x: 0.7, y: 0.55, w: 12, h: 0.4,
  fontFace: SANS, fontSize: 14, bold: true, color: CANARY,
  charSpacing: 12,
});
s1.addText("Do companies committing accounting fraud\nwrite their annual reports differently?", {
  x: 0.7, y: 1.3, w: 12, h: 1.8,
  fontFace: SERIF, fontSize: 36, color: "FFFFFF", italic: false, valign: "top", lineSpacingMultiple: 1.15,
});
rule(s1, 0.7, 3.4, 1.2, CANARY, 0.05);
s1.addText("A pre-registered novelty study on SEC 10-K filings.", {
  x: 0.7, y: 3.6, w: 12, h: 0.4,
  fontFace: SERIF, fontSize: 16, italic: true, color: "CFD8E8",
});

// AI model summary (what was trained vs what was reused)
s1.addText([
  { text: "Trained: ", options: { bold: true, color: CANARY } },
  { text: "five small autoencoders in PyTorch, one per held-out fraud cohort.", options: { color: "FFFFFF" } },
], { x: 0.7, y: 4.4, w: 12, h: 0.45, fontFace: SANS, fontSize: 15 });
s1.addText([
  { text: "Reused: ", options: { bold: true, color: CANARY } },
  { text: "a pretrained MiniLM transformer, frozen, as a sentence-to-vector encoder.", options: { color: "FFFFFF" } },
], { x: 0.7, y: 4.85, w: 12, h: 0.45, fontFace: SANS, fontSize: 15 });
s1.addText([
  { text: "Tested: ", options: { bold: true, color: CANARY } },
  { text: "six historical accounting frauds; methodology locked in git before any number was looked at.", options: { color: "FFFFFF" } },
], { x: 0.7, y: 5.3, w: 12, h: 0.45, fontFace: SANS, fontSize: 15 });

s1.addText([
  { text: "Arsenii Chan",   options: { bold: true, color: "FFFFFF" } },
  { text: "   ·   CSC 44800 Artificial Intelligence",   options: { color: "CFD8E8" } },
  { text: "   ·   Spring 2026 · CCNY",   options: { color: "CFD8E8" } },
], {
  x: 0.7, y: 6.5, w: 9, h: 0.4,
  fontFace: SANS, fontSize: 14,
});

// QR code pointing to the live demo (so the audience can try it on their phones)
s1.addImage({ path: FIG("qr_demo.png"), x: 11.4, y: 5.7, w: 1.3, h: 1.3 });
s1.addText("scan to try", {
  x: 11.2, y: 7.0, w: 1.7, h: 0.25,
  fontFace: SANS, fontSize: 9, italic: true, color: "CFD8E8", align: "center",
});
s1.addNotes(
`TARGET: 0:25.

SAY:
"I'm Arsenii Chan. The question I built this project around is a simple one: do companies that turn out to have been committing accounting fraud write their annual reports differently from honest companies, and can a machine learning model detect that difference? Six famous cases. One specific test. Let me show you what came back."

(Pause. Click to slide 2.)

STAGE NOTES:
- Don't announce the conclusion. Don't say "honestly" or "negative result"; both pre-spoil the talk.
- Open with the question. The audience leans forward.
- No jargon out loud: never say "autoencoder" or "MD&A" aloud. Keep them on the slide only.
- The slide shows just the first half of the question ("do they write differently"). You verbally complete it ("and can a model detect that"). The audience reads the slide while you fill in the rest.`
);

// ---------- Slide 2: Driving question ----------
const s2 = pres.addSlide();
s2.background = { color: SURFACE_2 };
eyebrow(s2, 0.7, 0.5, "THE DRIVING QUESTION");
rule(s2, 0.7, 0.95, 0.6);
s2.addText('"', {
  x: 0.6, y: 1.2, w: 1, h: 1.5,
  fontFace: SERIF, fontSize: 110, color: CANARY, bold: false,
});
s2.addText(
  "Does an unsupervised autoencoder trained on industry-and-year-matched clean 10-K MD&A text assign elevated reconstruction error to known historical fraud filings, under strictly out-of-sample evaluation?",
  {
    x: 1.7, y: 1.5, w: 11, h: 2.6,
    fontFace: SERIF, fontSize: 26, italic: true, color: NAVY_DARK, lineSpacingMultiple: 1.25,
  }
);
rule(s2, 0.7, 4.5, 1.2);
s2.addText("The one-line answer this report defends:", {
  x: 0.7, y: 4.7, w: 12, h: 0.4,
  fontFace: SANS, fontSize: 13, color: INK_2, bold: true,
});
s2.addText(
  "At N = 6 frauds, with strict pre-registration: no useful autoencoder signal across four of five evaluable cohorts; Enron is not evaluable under the frozen rule; the one cohort the autoencoder did rank highly (Lehman) is n = 1, and a 1990s TF-IDF baseline beats the autoencoder on it.",
  {
    x: 0.7, y: 5.15, w: 12, h: 1.7,
    fontFace: SERIF, fontSize: 18, color: INK, lineSpacingMultiple: 1.3,
  }
);
pageFooter(s2, 2, 7);
s2.addNotes(
`TARGET: 0:45.

SAY:
"Six historical fraud cases: Enron, WorldCom, Tyco, HealthSouth, Valeant, Lehman Brothers. Each one was later proven to have been misrepresenting its financial condition at the time of this filing. The SEC or class-action lawsuits exposed them years afterward; each cost investors over a billion dollars. I paired each fraud filing against companies in the same industry, same year, that turned out to be clean.

The model never sees the word 'fraud' during training. It just reads the long English-prose section of each annual report, where management explains the year in their own words, and learns what a 'normal' filing looks like industry by industry. Then it ranks the unusual filings against their peers.

The formal question is on the slide [point at pull-quote]. The one-line answer this report defends is on the next bullet [point at it]. I'll spend the rest of the talk on the evidence."

(Click to slide 3.)

STAGE NOTES:
- Don't read the pull-quote out loud. It's full of jargon and the audience can read it faster than you can speak it. Just point.
- Same with the one-line answer. Pointing is faster than reading.
- The "long English-prose section where management explains the year" is the plain-English explanation of MD&A. Don't say "MD&A" out loud unless someone asks — the slide pull-quote shows the formal name for the technical reader.
- The context line about each cohort being a multi-billion-dollar fraud is critical for audience comprehension. By the time they reach slide 4 they need to know these names matter. Don't skip it.`
);

// ---------- Slide 3: The methodological contract (the lede) ----------
const s3 = pres.addSlide();
s3.background = { color: SURFACE };
eyebrow(s3, 0.7, 0.5, "THE METHODOLOGICAL CONTRACT");
rule(s3, 0.7, 0.95, 0.6);
s3.addText("The contract is the contribution.", {
  x: 0.7, y: 1.1, w: 12, h: 0.7,
  fontFace: SERIF, fontSize: 32, bold: true, color: NAVY_DARK,
});
s3.addText("git-tagged validation-spec-frozen, committed before any validation script ran.", {
  x: 0.7, y: 1.85, w: 12, h: 0.4,
  fontFace: SANS, fontSize: 14, italic: true, color: INK_2,
});

// Three rules, prose labels (no numbered listicle)
const colY = 2.6;
const colH = 3.6;
const colW = 4.0;
const cols = [
  {
    x: 0.7, label: "Out-of-sample, always",
    body: "Leave-one-cohort-out (LOCO): for each held-out fraud, the autoencoder is trained on clean filings from other cohorts only. The fraud and its peers are never in the training set."
  },
  {
    x: 4.7, label: "Time-controlled training",
    body: "Within the LOCO training set, only filings dated on or before that fraud's filing date are eligible. The autoencoder's training corpus cannot include post-fraud disclosure language. (MiniLM pretraining is a separate caveat.)"
  },
  {
    x: 8.7, label: "Single pass, no tuning",
    body: "Architecture, hyperparameters, sentence cap, seeds: all committed and tagged before validation ran. scripts/06_validate.py runs once. No model tuning after validation."
  },
];
cols.forEach((c) => {
  s3.addShape(pres.ShapeType.rect, {
    x: c.x, y: colY, w: colW, h: colH,
    fill: { color: SURFACE_2 }, line: { color: RULE, width: 0.5 },
  });
  s3.addText(c.label, {
    x: c.x + 0.25, y: colY + 0.2, w: colW - 0.5, h: 0.4,
    fontFace: SANS, fontSize: 11, bold: true, color: CANARY, charSpacing: 3,
  });
  rule(s3, c.x + 0.25, colY + 0.65, 0.4);
  s3.addText(c.body, {
    x: c.x + 0.25, y: colY + 0.85, w: colW - 0.5, h: colH - 1.0,
    fontFace: SERIF, fontSize: 13, color: INK, lineSpacingMultiple: 1.35,
  });
});
s3.addText(
  "Whatever the test produces, the contract makes the result interpretable.",
  {
    x: 0.7, y: 6.4, w: 8.0, h: 0.5,
    fontFace: SERIF, fontSize: 14, italic: true, color: NAVY,
  }
);
// Forensic evidence of pre-registration: git tag, hash, timestamp
s3.addShape(pres.ShapeType.rect, {
  x: 8.9, y: 6.35, w: 4.0, h: 0.55,
  fill: { color: SURFACE_2 }, line: { color: NAVY_LIGHT, width: 0.5 },
});
s3.addText([
  { text: "git tag: ", options: { fontSize: 9, color: INK_3 } },
  { text: "validation-spec-frozen", options: { fontSize: 9, bold: true, color: NAVY } },
  { text: "\nat 98d2585  ·  2026-05-01 13:42:42 EDT", options: { fontSize: 9, color: INK_3 } },
], {
  x: 9.05, y: 6.4, w: 3.7, h: 0.5,
  fontFace: "Consolas", lineSpacingMultiple: 1.3,
});
pageFooter(s3, 3, 7);
s3.addNotes(
`TARGET: 0:50. THIS IS THE MOST IMPORTANT SLIDE. SLOW DOWN.

SAY:
"Before I show you any number, I want to put the methodology on the table. The methodology is what makes the result mean anything.

Three rules I locked in BEFORE I ran the test. [point at columns]

One: the model never sees a fraud during training. For each fraud case, the model trains on clean filings from OTHER cases. The fraud being tested is held out.

Two: the model never sees the future. Within that training set, only filings dated on or before the fraud's filing date are eligible. The model can't be informed by language that came out AFTER the fraud was discovered.

Three: single pass, no tuning. Architecture, hyperparameters, the test set: all written down and locked into the repo BEFORE the test ran. [point at git-tag panel:] Top right shows the actual lock, committed and tagged on May 1st, before any result came in.

Test ran once. Whatever it said, that's the result."

(Click to slide 4.)

STAGE NOTES:
- The git-tag panel is small. Say "top right shows" rather than gesturing at the podium.
- If anyone in the room knows what pre-registration is, this is where you've already won them over.
- Avoid jargon: don't say "LOCO" or "MiniLM" aloud. Say "leave-one-out" or "the embedding model" if pressed.`
);

// ---------- Slide 4: Per-fraud results ----------
const s4 = pres.addSlide();
s4.background = { color: SURFACE_2 };
eyebrow(s4, 0.7, 0.5, "RESULTS · 5 OF 6 COHORTS · ENRON EXCLUDED BY THE RULE");
rule(s4, 0.7, 0.95, 0.6);
s4.addText("Only Lehman ranks better than random expectation; even there, a 1990s baseline beats the autoencoder.", {
  x: 0.7, y: 1.1, w: 12, h: 0.6,
  fontFace: SERIF, fontSize: 22, bold: true, color: NAVY_DARK,
});

// Table: per-fraud results (rank only; statistical detail moves to speaker notes)
const tableData = [
  [
    { text: "Cohort",      options: { bold: true, fill: NAVY_DARK, color: "FFFFFF", align: "left" } },
    { text: "Rank",        options: { bold: true, fill: NAVY_DARK, color: "FFFFFF", align: "center" } },
    { text: "Note",        options: { bold: true, fill: NAVY_DARK, color: "FFFFFF", align: "left" } },
  ],
  [
    { text: "Lehman (LEH, FY 2007)  ⚠", options: { bold: true, color: NAVY_DARK } },
    { text: "3 / 13",                    options: { align: "center", bold: true, color: NAVY_DARK } },
    { text: "n = 1, baseline beats autoencoder",  options: { italic: true, color: INK_2 } },
  ],
  [
    { text: "HealthSouth (HRC)", options: {} },
    { text: "7 / 12",            options: { align: "center" } },
    { text: "at or below random",  options: { color: INK_2 } },
  ],
  [
    { text: "Valeant (VRX)",     options: {} },
    { text: "8 / 13",            options: { align: "center" } },
    { text: "at or below random",  options: { color: INK_2 } },
  ],
  [
    { text: "Tyco (TYC)",        options: {} },
    { text: "9 / 13",            options: { align: "center" } },
    { text: "at or below random",  options: { color: INK_2 } },
  ],
  [
    { text: "WorldCom (WCOM)",   options: {} },
    { text: "12 / 13",           options: { align: "center" } },
    { text: "at or below random",  options: { color: INK_2 } },
  ],
  [
    { text: "Enron (ENE, FY 2000)", options: { italic: true, color: INK_2 } },
    { text: "—",                    options: { align: "center", italic: true, color: INK_2 } },
    { text: "not evaluable: filed earliest, no eligible training data", options: { italic: true, color: INK_2 } },
  ],
];
s4.addTable(tableData, {
  x: 0.7, y: 1.95, w: 8.0, h: 3.5,
  fontFace: SANS, fontSize: 13, color: INK,
  border: { type: "solid", pt: 0.5, color: RULE },
  rowH: [0.4, 0.45, 0.45, 0.45, 0.45, 0.45, 0.45],
  colW: [2.8, 1.2, 4.0],
});

// Side panel: the framing
s4.addShape(pres.ShapeType.rect, {
  x: 8.95, y: 1.95, w: 3.85, h: 3.5,
  fill: { color: SURFACE }, line: { color: RULE, width: 0.5 },
});
s4.addText("Aggregate hit-rates", {
  x: 9.15, y: 2.1, w: 3.5, h: 0.3,
  fontFace: SANS, fontSize: 11, bold: true, color: NAVY_LIGHT, charSpacing: 3,
});
rule(s4, 9.15, 2.45, 0.4, NAVY_LIGHT);
s4.addText([
  { text: "hit@1: ",  options: { fontFace: SANS, fontSize: 13, color: INK_2 } },
  { text: "0.00",     options: { fontFace: SANS, fontSize: 18, bold: true, color: INK } },
  { text: "  vs random 0.08\n", options: { fontFace: SANS, fontSize: 11, color: INK_3 } },
  { text: "hit@3: ",  options: { fontFace: SANS, fontSize: 13, color: INK_2 } },
  { text: "0.20",     options: { fontFace: SANS, fontSize: 18, bold: true, color: INK } },
  { text: "  vs random 0.23\n", options: { fontFace: SANS, fontSize: 11, color: INK_3 } },
  { text: "hit@5: ",  options: { fontFace: SANS, fontSize: 13, color: INK_2 } },
  { text: "0.20",     options: { fontFace: SANS, fontSize: 18, bold: true, color: INK } },
  { text: "  vs random 0.39", options: { fontFace: SANS, fontSize: 11, color: INK_3 } },
], { x: 9.15, y: 2.65, w: 3.5, h: 2.6, lineSpacingMultiple: 1.5 });

s4.addText(
  "⚠ Lehman is the only rank better than random expectation, and a 1990s baseline beats the autoencoder there too (slide 5). The aggregate is entirely Lehman.",
  {
    x: 0.7, y: 5.7, w: 12, h: 0.8,
    fontFace: SERIF, fontSize: 13, italic: true, color: INK_2, lineSpacingMultiple: 1.3,
  }
);
pageFooter(s4, 4, 7);
s4.addNotes(
`TARGET: 1:00.

SAY:
"Here's what came back. Five cases evaluable, one excluded; I'll come back to the excluded one.

[point at Lehman row] Only Lehman — the investment bank whose collapse triggered the 2008 financial crisis — lands in the top three within its peer group. Three out of thirteen. The statistical test is highly significant, BUT the effect size is small [point at warning glyph]. Both numbers matter; reporting either one alone is misleading. And as you'll see on the next slide, even on Lehman, a 1990s baseline beats my model.

[quick scan with hand] The other four (HealthSouth, Valeant, Tyco, WorldCom) all rank no better than random expectation. The test goes the OPPOSITE direction from what we'd want. Aggregate hit rates fall at or below random.

Now, Enron. [point at italicized row] Enron's filing date is April 2nd, 2001. Every other peer in every other case is dated later. Under the strict rule I locked in, Enron has no eligible training data.

So I had a choice: relax the rule and rerun, or report the exclusion. I reported the exclusion. The pre-registered design was infeasible for Enron, and I didn't catch that before I locked the spec. That's a finding about pre-registration, not about fraud detection."

(Click to slide 5.)

STAGE NOTES:
- Hands ON the slide. Don't quote numbers from memory; point at them on the projection.
- The forward-pointer line ("a 1990s baseline beats my model") is critical. If a listener tunes out during slide 5, they need to walk away with this on slide 4. Don't skip it.
- The Enron exclusion is the most likely Q&A target. Pre-empt it: "I had a choice: relax the rule or report the exclusion. I reported the exclusion."`
);

// ---------- Slide 5: Trivial baseline ----------
const s5 = pres.addSlide();
s5.background = { color: SURFACE_2 };
eyebrow(s5, 0.7, 0.5, "THE BASELINE CHECK · TF-IDF + SVD32 (POST-HOC)");
rule(s5, 0.7, 0.95, 0.6);
s5.addText("A 1990s baseline matched or beat the autoencoder on every cohort.", {
  x: 0.7, y: 1.1, w: 12, h: 0.5,
  fontFace: SERIF, fontSize: 24, bold: true, color: NAVY_DARK,
});
s5.addText("Post-hoc: tests whether the autoencoder earned its complexity, does not rescue the primary result.", {
  x: 0.7, y: 1.65, w: 12, h: 0.35,
  fontFace: SANS, fontSize: 12, italic: true, color: INK_2,
});
s5.addImage({ path: FIG("ae_vs_tfidf_rank.png"), x: 1.5, y: 2.15, w: 10.3, h: 4.0 });
s5.addText(
  "How to read the chart: shorter bar = lower rank number = better detection (rank 1 is most anomalous). Lehman: autoencoder rank 3/13, TF-IDF rank 1/13. Aggregate hit@5 is 0.40 (TF-IDF) vs 0.20 (autoencoder). The pre-registered model does not beat the trivial baseline.",
  {
    x: 0.7, y: 6.25, w: 12, h: 0.7,
    fontFace: SERIF, fontSize: 13, italic: true, color: INK, lineSpacingMultiple: 1.3,
  }
);
pageFooter(s5, 5, 7);
s5.addNotes(
`TARGET: 1:10. THIS IS THE LEDE OF THE TALK. DON'T RUSH.

SAY:
"Now the part that I think actually matters.

After the test ran, I asked myself the question every machine-learning paper should answer and most don't: would a method from before I was born produce the same result?

So I ran one. [point at chart] A simple word-counting method with the same compression step. The kind of thing you could have written in 1995 from a textbook. Same training data, same statistical tests, same pipeline shape. No neural network. No transformer.

[point at chart] On four of five cases, the 1995 method TIES the modern one. [point at Lehman bar] On Lehman, the one case the modern method got, the 1995 method gets it BETTER. The p-value is many orders of magnitude smaller.

Let me say what I'm not saying and then what I am saying.

I am NOT saying the modern method is broken, or that neural networks are unhelpful for this kind of problem.

I AM saying that on these five cases, with the rules I locked in, the modern method did not show a measurable advantage over a method I could have run in 1995.

If you take one thing from this talk, this is it: a sharp baseline isn't optional. A result that loses to a baseline is not evidence for the neural model."

(Click to slide 6.)

STAGE NOTES:
- The "before I was born" / "1995" framing is the kill line. Practice deadpan delivery.
- If the room is silent after, that's fine. Keep going.
- The "I am not saying / I am saying" structure prevents the misread "the AI didn't work."
- Don't say "TF-IDF" or "truncated SVD" aloud unless someone asks. "1995 method" or "simple word-counting method" is the spoken phrase. The slide and chart already show the technical names.`
);

// ---------- Slide 6: Anticipated questions (Q&A defense) ----------
const s6 = pres.addSlide();
s6.background = { color: SURFACE };
eyebrow(s6, 0.7, 0.5, "QUESTIONS I EXPECT");
rule(s6, 0.7, 0.95, 0.6);

const qa = [
  {
    q: "Did you check a trivial baseline?",
    a: "Yes. TF-IDF + truncated-SVD, same bottleneck dimension, same training corpora. It matches or beats the autoencoder on every cohort. The honest claim is that the autoencoder adds nothing here. Slide 5."
  },
  {
    q: "The baseline is post-hoc. Isn't that HARKing (hypothesizing after results)?",
    a: "The pre-registered hypothesis was about the autoencoder, and the autoencoder result is reported unchanged. The TF-IDF baseline was added after seeing the null and is reported as post-hoc. The primary null does not depend on it."
  },
  {
    q: "Could MiniLM have memorized 'Lehman' / 'Repo 105' / etc.?",
    a: "Tested post-hoc. Masked 93 such mentions with [ENTITY] and re-scored. Lehman's rank held at 3/13 (delta = 0). Exact-token name leakage did not explain the rank; topical leakage remains open."
  },
];
const qaY = 1.3;
const qaH = 1.7;
qa.forEach((item, i) => {
  const y = qaY + i * (qaH + 0.1);
  s6.addShape(pres.ShapeType.rect, {
    x: 0.7, y, w: 12.1, h: qaH,
    fill: { color: SURFACE_2 }, line: { color: RULE, width: 0.5 },
  });
  rule(s6, 0.7, y, 0.04, CANARY, qaH); // left accent
  s6.addText("Q", {
    x: 0.85, y: y + 0.1, w: 0.5, h: 0.4,
    fontFace: SERIF, fontSize: 18, bold: true, color: CANARY,
  });
  s6.addText(item.q, {
    x: 1.4, y: y + 0.1, w: 11.0, h: 0.4,
    fontFace: SANS, fontSize: 14, bold: true, color: NAVY_DARK,
  });
  s6.addText(item.a, {
    x: 1.4, y: y + 0.5, w: 11.2, h: qaH - 0.55,
    fontFace: SERIF, fontSize: 12, color: INK, lineSpacingMultiple: 1.3,
  });
});
pageFooter(s6, 6, 7);
s6.addNotes(
`TARGET: 0:40. SPEED.

SAY:
"Three questions I expect, with quick answers so we have time for whatever else you actually want to ask.

Did you check a trivial baseline? Yes. Same compression dimension, same training data. The 1995 baseline matches or beats the modern method on every case. The honest claim is that the modern method adds nothing here. Slide 5.

The baseline is post-hoc, isn't that HARKing? The pre-registered hypothesis was about the modern method, and that result is reported unchanged. The 1995 baseline was added after seeing the null and is reported as post-hoc. The primary null doesn't depend on it.

Could the embedding model have memorized 'Lehman' or 'Repo 105'? I tested that. I masked 93 such mentions in Lehman's filing with a placeholder and re-scored. Lehman's rank held at 3 out of 13. Exact-token name leakage doesn't explain the rank."

(Click to slide 7.)

STAGE NOTES:
- Three Q&As live on slide. The Enron exclusion question is best handled in actual Q&A if asked (already covered on slide 4).
- Don't try to deliver all three under pressure if you're running long. Two minimum.
- If asked about supervised classifier: "At six fraud examples a supervised classifier overfits trivially. Future work."
- If asked about the parser: "Five failures are pre-2001 peer filings. All six fraud filings parsed at 100%."`
);

// ---------- Slide 7: Conclusion + next experiment + repo + thanks ----------
const s7 = pres.addSlide();
s7.background = { color: NAVY_DARK };
s7.addText("CONCLUSION", {
  x: 0.7, y: 0.55, w: 12, h: 0.4,
  fontFace: SANS, fontSize: 12, bold: true, color: CANARY, charSpacing: 4,
});
rule(s7, 0.7, 1.0, 0.6, CANARY);

s7.addText("What survived: pre-registration.", {
  x: 0.7, y: 1.4, w: 10.5, h: 0.7,
  fontFace: SERIF, fontSize: 28, bold: true, color: "FFFFFF",
});
s7.addText("What failed: the autoencoder beyond the TF-IDF baseline.", {
  x: 0.7, y: 2.1, w: 10.5, h: 0.7,
  fontFace: SERIF, fontSize: 28, bold: true, color: "FFFFFF",
});

s7.addText(
  "A result that loses to a baseline is not evidence for the neural model. The contract held; the model did not.",
  {
    x: 0.7, y: 3.1, w: 10.5, h: 0.7,
    fontFace: SERIF, fontSize: 14, italic: true, color: "CFD8E8", lineSpacingMultiple: 1.3,
  }
);

s7.addText("What I'd do differently", {
  x: 0.7, y: 4.0, w: 10.5, h: 0.3,
  fontFace: SANS, fontSize: 11, bold: true, color: CANARY, charSpacing: 4,
});
rule(s7, 0.7, 4.35, 0.4, CANARY);
s7.addText(
  "Confirm every held-out fraud is evaluable under the pre-registered rule BEFORE freezing the spec. Enron taught that the hard way.",
  {
    x: 0.7, y: 4.5, w: 10.5, h: 0.6,
    fontFace: SERIF, fontSize: 13, color: "FFFFFF", lineSpacingMultiple: 1.3,
  }
);

s7.addText("Next experiment", {
  x: 0.7, y: 5.25, w: 10.5, h: 0.3,
  fontFace: SANS, fontSize: 11, bold: true, color: CANARY, charSpacing: 4,
});
rule(s7, 0.7, 5.6, 0.4, CANARY);
s7.addText(
  "Same autoencoder, within-firm temporal delta. Does Lehman's MD&A look anomalous against Lehman's own prior-year MD&A?",
  {
    x: 0.7, y: 5.75, w: 10.5, h: 0.55,
    fontFace: SERIF, fontSize: 13, color: "FFFFFF", lineSpacingMultiple: 1.3,
  }
);

// QR code (links to the live pipeline demo) — right side
s7.addText("Scan to try the pipeline", {
  x: 11.0, y: 3.85, w: 2.0, h: 0.25,
  fontFace: SANS, fontSize: 10, italic: true, color: "CFD8E8", align: "center",
});
s7.addImage({ path: FIG("qr_demo.png"), x: 11.3, y: 4.15, w: 1.4, h: 1.4 });

s7.addText([
  { text: "Pipeline demo (not a fraud scanner): ", options: { color: "CFD8E8" } },
  { text: "canary-psi.vercel.app/scan", options: { color: CANARY, bold: true } },
], { x: 0.7, y: 6.55, w: 12, h: 0.25, fontFace: SANS, fontSize: 11 });
s7.addText([
  { text: "Code: ", options: { color: "CFD8E8" } },
  { text: "github.com/ArseniiChan/canary", options: { color: CANARY, bold: true } },
  { text: "    ·    Tag: ", options: { color: "CFD8E8" } },
  { text: "validation-spec-frozen", options: { color: CANARY, bold: true } },
], { x: 0.7, y: 6.85, w: 12, h: 0.25, fontFace: SANS, fontSize: 11 });
s7.addText("Thanks.", {
  x: 0.7, y: 7.2, w: 12, h: 0.25,
  fontFace: SERIF, fontSize: 13, italic: true, color: "FFFFFF",
});
s7.addNotes(
`TARGET: 0:50. LAND THE URLs CLEANLY. PAUSE ONE BEAT AFTER "THANKS."

SAY:
"Two takeaways.

What survived: pre-registration. The contract held. I didn't iterate the model, I didn't redefine 'clean,' I didn't retreat from the Enron exclusion when the result was uncomfortable.

What failed: the modern method beyond the 1990s baseline. A result that loses to a baseline is not evidence for the neural model.

What I'd do differently: confirm every held-out fraud is actually evaluable under the rule BEFORE freezing the spec. Enron was unevaluable under my own rule, and I didn't catch it until validation ran.

Next experiment: same model, same filings, but compare each company against ITSELF across years instead of against peers. That's the falsifiable next step this study couldn't run.

[point at footer] Try the pipeline at the link below: paste any annual report, see how it scores against the five fraud cases. Code is on GitHub. The frozen-spec git tag is in the repo.

Thanks. Happy to take questions."

(End. Open Q&A.)

STAGE NOTES:
- Pause for ONE beat after "Thanks." Don't run into the next sentence.
- Look UP at the audience for the URL line. That's the call-to-action.
- If you've delivered slides 1 through 7 cleanly, your face should look calm.

Q&A FALLBACK LINE if you don't know an answer:
"That's a real gap I haven't characterized. Let me follow up after the talk."

Don't fake numbers under pressure. "I don't know" is graduate-school behavior, not weakness.

TIME TARGETS:
Slide 1: 0:25  |  Slide 2: 0:45  |  Slide 3: 0:50  |  Slide 4: 1:00
Slide 5: 1:10  |  Slide 6: 0:40  |  Slide 7: 0:45
Total target: 5:35.  Hard ceiling: 6:55.  Buffer: 1:25.

IF RUNNING LONG, CUTS:
- Drop "I am not saying / I am saying" on Slide 5 (saves 15 seconds)
- Skip third Q&A on Slide 6 (saves 15 seconds)
- Skip next-experiment line on Slide 7 (saves 10 seconds)`
);

// ---------- Save ----------
pres.writeFile({ fileName: OUT })
  .then((p) => console.log(`wrote ${p}`))
  .catch((e) => { console.error(e); process.exit(1); });
