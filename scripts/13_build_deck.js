#!/usr/bin/env node
/* eslint-disable */
// Build canary deck (7 slides) ordering:
//   1. Title
//   2. Driving question (pull quote)
//   3. The methodological contract  (the LEDE, not the result)
//   4. Per-fraud results — Lehman + others + Enron exclusion in one frame
//   5. The trivial baseline matched/exceeded the autoencoder
//   6. Anticipated questions (Q&A defense — pre-empt TF-IDF, Enron, ablation)
//   7. Conclusions + repo + thanks
//
// 13.33" × 7.5" widescreen. Run with NODE_PATH=$(npm root -g).

const path = require("path");
const PptxGenJS = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const FIG = (n) => path.join(ROOT, "reports/figures", n);
const OUT = path.join(ROOT, "reports/canary_deck.pptx");

const pres = new PptxGenJS();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.title = "Canary — Pre-Registered Single-Signal Novelty Study on SEC 10-K MD&A";
pres.author = "Arsenii Chan";
pres.company = "CSC 44800 — CCNY — Spring 2026";

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
s1.addText("Can a computer reading the words in a 10-K\nflag the companies that turned out to be frauds?", {
  x: 0.7, y: 2.1, w: 12, h: 2.1,
  fontFace: SERIF, fontSize: 36, color: "FFFFFF", italic: false, valign: "top", lineSpacingMultiple: 1.15,
});
rule(s1, 0.7, 4.5, 1.2, CANARY, 0.05);
s1.addText("A pre-registered single-signal novelty study on SEC 10-K MD&A text.", {
  x: 0.7, y: 4.7, w: 12, h: 0.5,
  fontFace: SERIF, fontSize: 18, italic: true, color: "CFD8E8",
});
s1.addText(
  "Primary contribution: a pre-registered null result with a baseline that beat the proposed model — exactly the artifact the field claims to want and rarely produces.",
  {
    x: 0.7, y: 5.25, w: 12, h: 0.7,
    fontFace: SERIF, fontSize: 14, italic: true, color: CANARY, lineSpacingMultiple: 1.25,
  }
);
s1.addText([
  { text: "Arsenii Chan",   options: { bold: true, color: "FFFFFF" } },
  { text: "   ·   CSC 44800 — Artificial Intelligence",   options: { color: "CFD8E8" } },
  { text: "   ·   Spring 2026 · CCNY",   options: { color: "CFD8E8" } },
], {
  x: 0.7, y: 6.3, w: 12, h: 0.4,
  fontFace: SANS, fontSize: 14,
});
s1.addText([
  { text: "Live demo: ", options: { color: "CFD8E8" } },
  { text: "canary-psi.vercel.app", options: { color: CANARY, bold: true } },
  { text: "    ·    Code: ", options: { color: "CFD8E8" } },
  { text: "github.com/ArseniiChan/canary", options: { color: CANARY } },
], {
  x: 0.7, y: 6.7, w: 12, h: 0.3,
  fontFace: SANS, fontSize: 11,
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
  "At N = 6 frauds, with strict pre-registration: NO for four of five evaluable cohorts, NO for Enron (excluded by the rule itself), and the one cohort that ranks high (Lehman) is matched or exceeded by a 1990s TF-IDF baseline.",
  {
    x: 0.7, y: 5.15, w: 12, h: 1.7,
    fontFace: SERIF, fontSize: 18, color: INK, lineSpacingMultiple: 1.3,
  }
);
pageFooter(s2, 2, 7);

// ---------- Slide 3: The methodological contract (the lede) ----------
const s3 = pres.addSlide();
s3.background = { color: SURFACE };
eyebrow(s3, 0.7, 0.5, "THE LEDE — METHODOLOGICAL CONTRACT");
rule(s3, 0.7, 0.95, 0.6);
s3.addText("The work is the contract", {
  x: 0.7, y: 1.1, w: 12, h: 0.7,
  fontFace: SERIF, fontSize: 32, bold: true, color: NAVY_DARK,
});
s3.addText("git-tagged validation-spec-frozen — committed before any validation script ran", {
  x: 0.7, y: 1.85, w: 12, h: 0.4,
  fontFace: SANS, fontSize: 14, italic: true, color: INK_2,
});

// Three columns for the rules
const colY = 2.6;
const colH = 3.6;
const colW = 4.0;
const cols = [
  {
    x: 0.7, label: "01 — Out-of-sample, always",
    body: "Leave-one-cohort-out: for each held-out fraud, the autoencoder is trained on clean filings from OTHER cohorts only. The fraud and its peers are never in the training set. Without this, peers carry an in-sample reconstruction-error advantage."
  },
  {
    x: 4.7, label: "02 — Time-controlled training",
    body: "Within the LOCO training set, only filings dated ≤ that fraud's filing date are eligible. The model's representation of \"clean\" cannot be contaminated by post-fraud disclosure language."
  },
  {
    x: 8.7, label: "03 — Single pass, no tuning",
    body: "Architecture, hyperparameters, sentence cap, seeds — all committed and tagged before validation ran. scripts/06_validate.py runs ONCE. Whatever the numbers say, that is the result. No iteration, no excuses."
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
  "If the contract holds, the result is informative whatever the numbers say. The discipline IS the deliverable.",
  {
    x: 0.7, y: 6.4, w: 8.0, h: 0.5,
    fontFace: SERIF, fontSize: 14, italic: true, color: NAVY,
  }
);
// Forensic evidence of pre-registration — the actual git tag, hash, timestamp
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
eyebrow(s4, 0.7, 0.5, "RESULTS — 5 OF 6 COHORTS, ENRON EXCLUDED BY THE RULE");
rule(s4, 0.7, 0.95, 0.6);
s4.addText("One detectable. Four indistinguishable. One excluded by design.", {
  x: 0.7, y: 1.1, w: 12, h: 0.6,
  fontFace: SERIF, fontSize: 26, bold: true, color: NAVY_DARK,
});

// Table: per-fraud results
const tableData = [
  [
    { text: "Cohort",      options: { bold: true, fill: NAVY_DARK, color: "FFFFFF", align: "left" } },
    { text: "Rank",        options: { bold: true, fill: NAVY_DARK, color: "FFFFFF", align: "center" } },
    { text: "MW p",        options: { bold: true, fill: NAVY_DARK, color: "FFFFFF", align: "center" } },
    { text: "Effect",      options: { bold: true, fill: NAVY_DARK, color: "FFFFFF", align: "center" } },
    { text: "95% CI",      options: { bold: true, fill: NAVY_DARK, color: "FFFFFF", align: "center" } },
    { text: "Train sents", options: { bold: true, fill: NAVY_DARK, color: "FFFFFF", align: "center" } },
  ],
  [
    { text: "Lehman (LEH) — FY2007  ⚑", options: { bold: true, color: NAVY_DARK } },
    { text: "3 / 13",          options: { align: "center", bold: true, color: NAVY_DARK } },
    { text: "1.3 × 10⁻⁹",      options: { align: "center" } },
    { text: "+0.12 (small)",   options: { align: "center" } },
    { text: "[1, 6]",          options: { align: "center" } },
    { text: "3,367",           options: { align: "center" } },
  ],
  [
    { text: "HealthSouth (HRC)", options: {} },
    { text: "7 / 12",      options: { align: "center" } },
    { text: "1.0",         options: { align: "center" } },
    { text: "−0.17",       options: { align: "center" } },
    { text: "[4, 10]",     options: { align: "center" } },
    { text: "2,283",       options: { align: "center" } },
  ],
  [
    { text: "Valeant (VRX)", options: {} },
    { text: "8 / 13",      options: { align: "center" } },
    { text: "1.0",         options: { align: "center" } },
    { text: "−0.19",       options: { align: "center" } },
    { text: "[5, 11]",     options: { align: "center" } },
    { text: "4,327",       options: { align: "center" } },
  ],
  [
    { text: "Tyco (TYC)", options: {} },
    { text: "9 / 13",      options: { align: "center" } },
    { text: "1.0",         options: { align: "center" } },
    { text: "−0.14",       options: { align: "center" } },
    { text: "[6, 12]",     options: { align: "center" } },
    { text: "861",         options: { align: "center" } },
  ],
  [
    { text: "WorldCom (WCOM)", options: {} },
    { text: "12 / 13",     options: { align: "center" } },
    { text: "1.0",         options: { align: "center" } },
    { text: "−0.15",       options: { align: "center" } },
    { text: "[10, 13]",    options: { align: "center" } },
    { text: "1,477",       options: { align: "center" } },
  ],
  [
    { text: "Enron (ENE) — FY2000", options: { italic: true, color: INK_2 } },
    { text: "—",     options: { align: "center", italic: true, color: INK_2 } },
    { text: "—",     options: { align: "center", italic: true, color: INK_2 } },
    { text: "—",     options: { align: "center", italic: true, color: INK_2 } },
    { text: "—",     options: { align: "center", italic: true, color: INK_2 } },
    { text: "—",     options: { align: "center", italic: true, color: INK_2 } },
  ],
];
s4.addTable(tableData, {
  x: 0.7, y: 1.95, w: 8.0, h: 4.0,
  fontFace: SANS, fontSize: 12, color: INK,
  border: { type: "solid", pt: 0.5, color: RULE },
  rowH: [0.4, 0.45, 0.45, 0.45, 0.45, 0.45, 0.45],
  colW: [2.5, 1.0, 1.4, 1.0, 1.1, 1.0],
});

// Side panel: the framing
s4.addShape(pres.ShapeType.rect, {
  x: 8.95, y: 1.95, w: 3.85, h: 4.0,
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
], { x: 9.15, y: 2.65, w: 3.5, h: 1.6, lineSpacingMultiple: 1.5 });

s4.addText("Enron is excluded by the rule itself", {
  x: 9.15, y: 4.4, w: 3.5, h: 0.3,
  fontFace: SANS, fontSize: 11, bold: true, color: NAVY_LIGHT, charSpacing: 3,
});
rule(s4, 9.15, 4.75, 0.4, NAVY_LIGHT);
s4.addText(
  "Filed 2001-04-02 — earlier than every peer in every other cohort. LOCO + time-controlled admits no eligible training data. Exclusion IS the finding.",
  {
    x: 9.15, y: 4.95, w: 3.5, h: 1.0,
    fontFace: SERIF, fontSize: 12, color: INK, italic: true, lineSpacingMultiple: 1.3,
  }
);

s4.addText(
  "⚑ = Lehman is the only cohort above chance — but a 1990s baseline beats the autoencoder there too. See slide 5. Aggregate hit@k falls at or below random. The aggregate is entirely Lehman.",
  {
    x: 0.7, y: 6.15, w: 12, h: 0.6,
    fontFace: SERIF, fontSize: 13, italic: true, color: INK_2, lineSpacingMultiple: 1.2,
  }
);
pageFooter(s4, 4, 7);

// ---------- Slide 5: Trivial baseline ----------
const s5 = pres.addSlide();
s5.background = { color: SURFACE_2 };
eyebrow(s5, 0.7, 0.5, "THE BASELINE CHECK — TF-IDF + SVD32 (POST-HOC)");
rule(s5, 0.7, 0.95, 0.6);
s5.addText("A 1990s baseline matched or beat the autoencoder on every cohort.", {
  x: 0.7, y: 1.1, w: 12, h: 0.6,
  fontFace: SERIF, fontSize: 24, bold: true, color: NAVY_DARK,
});
s5.addImage({ path: FIG("ae_vs_tfidf_rank.png"), x: 0.6, y: 2.0, w: 6.4, h: 4.0 });
s5.addImage({ path: FIG("ae_vs_tfidf_mw.png"),   x: 7.2, y: 2.0, w: 6.0, h: 4.0 });
s5.addText(
  "On the one cohort with any signal at all, the 1990s baseline is stronger: rank 1/13 vs 3/13, p ≈ 5×10⁻²² vs 1.3×10⁻⁹, effect +0.19 vs +0.12. Aggregate hit@5 = 0.40 (TF-IDF) vs 0.20 (autoencoder). The pre-registered model is not the signal carrier.",
  {
    x: 0.7, y: 6.15, w: 12, h: 0.7,
    fontFace: SERIF, fontSize: 13, italic: true, color: INK, lineSpacingMultiple: 1.3,
  }
);
pageFooter(s5, 5, 7);

// ---------- Slide 6: Anticipated questions (Q&A defense) ----------
const s6 = pres.addSlide();
s6.background = { color: SURFACE };
eyebrow(s6, 0.7, 0.5, "ANTICIPATED QUESTIONS");
rule(s6, 0.7, 0.95, 0.6);
s6.addText("The questions a sharp reviewer asks first — pre-empted.", {
  x: 0.7, y: 1.1, w: 12, h: 0.6,
  fontFace: SERIF, fontSize: 24, bold: true, color: NAVY_DARK,
});

const qa = [
  {
    q: "Did you check a trivial baseline?",
    a: "Yes — TF-IDF + truncated-SVD with the same bottleneck dimension and the same training corpora. It matches or beats the autoencoder on every cohort. The honest claim is that the autoencoder adds nothing here. Slide 5."
  },
  {
    q: "Why is Enron excluded — isn't that convenient?",
    a: "The pre-registered LOCO + time-controlled rule admits no training data for Enron because it was filed earliest. The exclusion is the rule biting back. Owned as a design error in §7.1, not a workaround."
  },
  {
    q: "Lehman has the largest training corpus by 4× — is that the signal?",
    a: "Real confound, named in §8. The post-hoc TF-IDF baseline produces the same Lehman-specific result, weakly arguing against “training conditions alone.” I report Lehman as n=1 with the confound named, and decline to claim a method."
  },
  {
    q: "Could MiniLM have memorized 'Lehman' / 'Repo 105' / etc.?",
    a: "Tested post-hoc — masked 93 such mentions with [ENTITY] and re-scored. Lehman's rank held at 3/13 (delta = 0). Literal-name leakage rejected; topical leakage remains disclosed but unaddressed."
  },
];
const qaY = 1.95;
const qaH = 1.2;
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

// ---------- Slide 7: Conclusions + repo + thanks ----------
const s7 = pres.addSlide();
s7.background = { color: NAVY_DARK };
s7.addText("THREE THINGS THIS PROJECT TAUGHT ME", {
  x: 0.7, y: 0.55, w: 12, h: 0.4,
  fontFace: SANS, fontSize: 12, bold: true, color: CANARY, charSpacing: 4,
});
rule(s7, 0.7, 1.0, 0.6, CANARY);

const lessons = [
  {
    n: "01",
    h: "Pre-registration is load-bearing only if it survives contact with the data.",
    b: "The frozen spec held. I did not iterate the autoencoder, did not redefine “clean,” did not retreat from the Enron exclusion when the result was uncomfortable. Without that contract, the same numbers would be a polite request to redesign.",
  },
  {
    n: "02",
    h: "A sharp baseline is not optional.",
    b: "The most decisive result in this study is not the autoencoder's ranks but the post-hoc TF-IDF baseline matching them. A result that does not survive a baseline check is not a result.",
  },
  {
    n: "03",
    h: "If you own a design error, it becomes a checklist.",
    b: "Enron's exclusion was a design error caught by the freeze, not missing data. Pre-flight check for the next iteration: enumerate exclusions BEFORE freezing the contract, not after. Falsifiable next experiment: same autoencoder, within-firm temporal delta — does Lehman's MD&A look anomalous against Lehman's own prior-year MD&A?",
  },
];
lessons.forEach((l, i) => {
  const y = 1.4 + i * 1.5;
  s7.addText(l.n, {
    x: 0.7, y, w: 1.0, h: 0.7,
    fontFace: SANS, fontSize: 36, bold: true, color: CANARY,
  });
  s7.addText(l.h, {
    x: 1.7, y, w: 11, h: 0.6,
    fontFace: SERIF, fontSize: 18, bold: true, color: "FFFFFF",
  });
  s7.addText(l.b, {
    x: 1.7, y: y + 0.55, w: 11, h: 0.85,
    fontFace: SERIF, fontSize: 13, color: "CFD8E8", lineSpacingMultiple: 1.3,
  });
});

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
