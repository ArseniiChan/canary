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

// Palette: navy + canary yellow accent (the "canary" name)
const NAVY = "1A2B4C";
const NAVY_DARK = "0E1A33";
const NAVY_LIGHT = "5B7BB0";
const CANARY = "D4A017";       // muted canary yellow
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
  x: 0.7, y: 1.4, w: 12, h: 0.6,
  fontFace: SANS, fontSize: 14, bold: true, color: CANARY,
  charSpacing: 12,
});
s1.addText("Can a computer reading the words in a 10-K\nrank known fraud filings as anomalous?", {
  x: 0.7, y: 2.1, w: 12, h: 2.1,
  fontFace: SERIF, fontSize: 36, color: "FFFFFF", italic: false, valign: "top", lineSpacingMultiple: 1.15,
});
rule(s1, 0.7, 4.5, 1.2, CANARY, 0.05);
s1.addText("A pre-registered single-signal novelty study on SEC 10-K MD&A text.", {
  x: 0.7, y: 4.7, w: 12, h: 0.5,
  fontFace: SERIF, fontSize: 18, italic: true, color: "CFD8E8",
});
s1.addText(
  "Primary contribution: a pre-registered null result plus a baseline that beat the proposed model.",
  {
    x: 0.7, y: 5.25, w: 12, h: 0.7,
    fontFace: SERIF, fontSize: 14, italic: true, color: CANARY, lineSpacingMultiple: 1.25,
  }
);
s1.addText([
  { text: "Arsenii Chan",   options: { bold: true, color: "FFFFFF" } },
  { text: "   ·   CSC 44800 Artificial Intelligence",   options: { color: "CFD8E8" } },
  { text: "   ·   Spring 2026 · CCNY",   options: { color: "CFD8E8" } },
], {
  x: 0.7, y: 6.3, w: 12, h: 0.4,
  fontFace: SANS, fontSize: 14,
});

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
  "At N = 6 frauds, with strict pre-registration: no useful autoencoder signal across four of five evaluable cohorts; Enron is not evaluable under the frozen rule; the one cohort that ranks high (Lehman) is n = 1, and a 1990s TF-IDF baseline ranks it higher.",
  {
    x: 0.7, y: 5.15, w: 12, h: 1.7,
    fontFace: SERIF, fontSize: 18, color: INK, lineSpacingMultiple: 1.3,
  }
);
pageFooter(s2, 2, 7);

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
    body: "Leave-one-cohort-out. For each held-out fraud, the autoencoder is trained on clean filings from other cohorts only. The fraud and its peers are never in the training set."
  },
  {
    x: 4.7, label: "Time-controlled training",
    body: "Within the LOCO training set, only filings dated on or before that fraud's filing date are eligible. The model's representation of \"clean\" cannot include post-fraud disclosure language."
  },
  {
    x: 8.7, label: "Single pass, no tuning",
    body: "Architecture, hyperparameters, sentence cap, seeds: all committed and tagged before validation ran. scripts/06_validate.py runs once. Whatever the numbers say, that is the result."
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
  "The contract makes the null result interpretable, not conclusive.",
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

// ---------- Slide 4: Per-fraud results ----------
const s4 = pres.addSlide();
s4.background = { color: SURFACE_2 };
eyebrow(s4, 0.7, 0.5, "RESULTS · 5 OF 6 COHORTS · ENRON EXCLUDED BY THE RULE");
rule(s4, 0.7, 0.95, 0.6);
s4.addText("One high-ranked outlier. Four non-positive. One excluded by design.", {
  x: 0.7, y: 1.1, w: 12, h: 0.6,
  fontFace: SERIF, fontSize: 26, bold: true, color: NAVY_DARK,
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
    { text: "n = 1, baseline beats AE",  options: { italic: true, color: INK_2 } },
  ],
  [
    { text: "HealthSouth (HRC)", options: {} },
    { text: "7 / 12",            options: { align: "center" } },
    { text: "non-positive",      options: { color: INK_2 } },
  ],
  [
    { text: "Valeant (VRX)",     options: {} },
    { text: "8 / 13",            options: { align: "center" } },
    { text: "non-positive",      options: { color: INK_2 } },
  ],
  [
    { text: "Tyco (TYC)",        options: {} },
    { text: "9 / 13",            options: { align: "center" } },
    { text: "non-positive",      options: { color: INK_2 } },
  ],
  [
    { text: "WorldCom (WCOM)",   options: {} },
    { text: "12 / 13",           options: { align: "center" } },
    { text: "non-positive",      options: { color: INK_2 } },
  ],
  [
    { text: "Enron (ENE, FY 2000)", options: { italic: true, color: INK_2 } },
    { text: "—",                    options: { align: "center", italic: true, color: INK_2 } },
    { text: "not evaluable under the frozen rule", options: { italic: true, color: INK_2 } },
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
  "⚠ Lehman is the only rank better than random expectation, and a 1990s baseline ranks it higher (slide 5). The aggregate is entirely Lehman.",
  {
    x: 0.7, y: 5.7, w: 12, h: 0.8,
    fontFace: SERIF, fontSize: 13, italic: true, color: INK_2, lineSpacingMultiple: 1.3,
  }
);
pageFooter(s4, 4, 7);

// ---------- Slide 5: Trivial baseline ----------
const s5 = pres.addSlide();
s5.background = { color: SURFACE_2 };
eyebrow(s5, 0.7, 0.5, "THE BASELINE CHECK · TF-IDF + SVD32 (POST-HOC)");
rule(s5, 0.7, 0.95, 0.6);
s5.addText("A 1990s baseline matched or beat the autoencoder on every cohort.", {
  x: 0.7, y: 1.1, w: 12, h: 0.6,
  fontFace: SERIF, fontSize: 24, bold: true, color: NAVY_DARK,
});
s5.addImage({ path: FIG("ae_vs_tfidf_rank.png"), x: 1.5, y: 1.95, w: 10.3, h: 4.2 });
s5.addText(
  "Lehman: AE rank 3/13, TF-IDF rank 1/13. Aggregate hit@5 is 0.40 (TF-IDF) vs 0.20 (autoencoder). Mann-Whitney p is much smaller for TF-IDF on Lehman; exact values are in the report. The pre-registered model is not the signal carrier.",
  {
    x: 0.7, y: 6.25, w: 12, h: 0.7,
    fontFace: SERIF, fontSize: 13, italic: true, color: INK, lineSpacingMultiple: 1.3,
  }
);
pageFooter(s5, 5, 7);

// ---------- Slide 6: Anticipated questions (Q&A defense) ----------
const s6 = pres.addSlide();
s6.background = { color: SURFACE };
eyebrow(s6, 0.7, 0.5, "QUESTIONS I EXPECT");
rule(s6, 0.7, 0.95, 0.6);
s6.addText("Questions I expect.", {
  x: 0.7, y: 1.1, w: 12, h: 0.6,
  fontFace: SERIF, fontSize: 24, bold: true, color: NAVY_DARK,
});

const qa = [
  {
    q: "Did you check a trivial baseline?",
    a: "Yes. TF-IDF + truncated-SVD, same bottleneck dimension, same training corpora. It matches or beats the autoencoder on every cohort. The honest claim is that the autoencoder adds nothing here. Slide 5."
  },
  {
    q: "Why is Enron excluded; isn't that convenient?",
    a: "The pre-registered LOCO + time-controlled rule admits no training data for Enron because it was filed earliest. The exclusion is the rule biting back. I report Enron as a design failure, not a result."
  },
  {
    q: "Could MiniLM have memorized 'Lehman' / 'Repo 105' / etc.?",
    a: "Tested post-hoc. Masked 93 such mentions with [ENTITY] and re-scored. Lehman's rank held at 3/13 (delta = 0). Exact-token name leakage did not explain the rank; topical leakage remains open."
  },
];
const qaY = 1.95;
const qaH = 1.55;
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

// ---------- Slide 7: Conclusion + next experiment + repo + thanks ----------
const s7 = pres.addSlide();
s7.background = { color: NAVY_DARK };
s7.addText("CONCLUSION", {
  x: 0.7, y: 0.55, w: 12, h: 0.4,
  fontFace: SANS, fontSize: 12, bold: true, color: CANARY, charSpacing: 4,
});
rule(s7, 0.7, 1.0, 0.6, CANARY);

s7.addText("What survived: pre-registration.", {
  x: 0.7, y: 1.4, w: 12, h: 0.7,
  fontFace: SERIF, fontSize: 32, bold: true, color: "FFFFFF",
});
s7.addText("What failed: the autoencoder beyond the TF-IDF baseline.", {
  x: 0.7, y: 2.15, w: 12, h: 0.7,
  fontFace: SERIF, fontSize: 32, bold: true, color: "FFFFFF",
});

s7.addText(
  "A result that loses to a baseline is not evidence for the neural model. The contract held; the model did not.",
  {
    x: 0.7, y: 3.2, w: 12, h: 0.9,
    fontFace: SERIF, fontSize: 16, italic: true, color: "CFD8E8", lineSpacingMultiple: 1.3,
  }
);

s7.addText("Next experiment", {
  x: 0.7, y: 4.4, w: 12, h: 0.4,
  fontFace: SANS, fontSize: 12, bold: true, color: CANARY, charSpacing: 4,
});
rule(s7, 0.7, 4.8, 0.4, CANARY);
s7.addText(
  "Same autoencoder, within-firm temporal delta. Does Lehman's MD&A look anomalous against Lehman's own prior-year MD&A?",
  {
    x: 0.7, y: 5.0, w: 12, h: 0.9,
    fontFace: SERIF, fontSize: 16, color: "FFFFFF", lineSpacingMultiple: 1.3,
  }
);

s7.addText([
  { text: "Try it:  ", options: { color: "CFD8E8" } },
  { text: "canary-psi.vercel.app/scan", options: { color: CANARY, bold: true } },
  { text: "    ·    Code:  ", options: { color: "CFD8E8" } },
  { text: "github.com/ArseniiChan/canary", options: { color: CANARY, bold: true } },
  { text: "    ·    Tag:  ", options: { color: "CFD8E8" } },
  { text: "validation-spec-frozen", options: { color: CANARY, bold: true } },
], {
  x: 0.7, y: 6.5, w: 12, h: 0.4,
  fontFace: SANS, fontSize: 12,
});
s7.addText("Thanks.", {
  x: 0.7, y: 6.9, w: 12, h: 0.4,
  fontFace: SERIF, fontSize: 16, italic: true, color: "FFFFFF",
});

// ---------- Save ----------
pres.writeFile({ fileName: OUT })
  .then((p) => console.log(`wrote ${p}`))
  .catch((e) => { console.error(e); process.exit(1); });
