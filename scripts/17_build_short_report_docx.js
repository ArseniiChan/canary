#!/usr/bin/env node
/* eslint-disable */
// Build canary_report_short.docx — the 12-15 page submission body.
// Mirrors scripts/12_build_report_docx.js styling (Times New Roman 12pt
// double-spaced, US Letter, 1" margins, page numbers in footer) but
// uses ONLY the body content from canary_report_short.md and includes
// no Appendices F+G prose; figures are referenced not embedded.

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "reports/canary_report_short.docx");

const TIMES = "Times New Roman";
const BODY = 24;     // 12pt
const H1 = 32;
const H2 = 28;
const SMALL = 20;
const LINE = { line: 480, lineRule: "auto" }; // double-spaced
const SINGLE = { line: 240, lineRule: "auto" };

const border = (color = "000000") => ({ style: BorderStyle.SINGLE, size: 1, color });
const cellBorders = {
  top: border(), bottom: border(), left: border(), right: border(),
  insideHorizontal: border(), insideVertical: border(),
};
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

function p(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({ text, font: TIMES, size: opts.size || BODY, bold: opts.bold, italics: opts.italics })],
    spacing: opts.spacing || LINE,
    alignment: opts.alignment,
    indent: opts.indent,
  });
}

function image(file, widthIn) {
  const data = fs.readFileSync(path.join(ROOT, "reports/figures", file));
  const widthPx = (widthIn || 5.5) * 96;
  const heightPx = Math.round(widthPx * 0.625);
  const { ImageRun } = require("docx");
  return new Paragraph({
    children: [new ImageRun({
      type: "png", data,
      transformation: { width: widthPx, height: heightPx },
      altText: { title: file, description: file, name: file },
    })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 120, line: 240, lineRule: "auto" },
  });
}

function pBold(label, body) {
  return new Paragraph({
    children: [
      new TextRun({ text: label, font: TIMES, size: BODY, bold: true }),
      new TextRun({ text: body, font: TIMES, size: BODY }),
    ],
    spacing: LINE,
    indent: { firstLine: 360 },
  });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, font: TIMES, size: H1, bold: true })],
    spacing: { before: 360, after: 180, line: 280, lineRule: "auto" },
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text, font: TIMES, size: H2, bold: true })],
    spacing: { before: 280, after: 140, line: 280, lineRule: "auto" },
  });
}
function caption(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: TIMES, size: SMALL, italics: true })],
    spacing: SINGLE, alignment: AlignmentType.CENTER,
  });
}

function tableHeader(cells) {
  return new TableRow({
    tableHeader: true,
    children: cells.map((c) => new TableCell({
      borders: cellBorders, margins: cellMargins,
      shading: { fill: "EDEDED", type: ShadingType.CLEAR, color: "auto" },
      children: [new Paragraph({
        children: [new TextRun({ text: c, font: TIMES, size: SMALL, bold: true })],
        spacing: SINGLE,
      })],
    })),
  });
}
function tableRow(cells) {
  return new TableRow({
    children: cells.map((c) => new TableCell({
      borders: cellBorders, margins: cellMargins,
      children: [new Paragraph({
        children: [new TextRun({ text: String(c), font: TIMES, size: SMALL })],
        spacing: SINGLE,
      })],
    })),
  });
}
function buildTable(headers, rows, columnWidths) {
  return new Table({
    width: { size: columnWidths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    columnWidths,
    rows: [tableHeader(headers), ...rows.map(tableRow)],
  });
}

const children = [];

// Title block
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 0, after: 120, line: 280, lineRule: "auto" },
  children: [new TextRun({
    text: "Canary — A Pre-Registered Single-Signal Novelty Study on SEC 10-K MD&A Text",
    font: TIMES, size: 32, bold: true,
  })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: SINGLE,
  children: [new TextRun({ text: "Arsenii Chan", font: TIMES, size: BODY, bold: true })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: SINGLE,
  children: [new TextRun({ text: "CSC 44800 — Artificial Intelligence", font: TIMES, size: BODY })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: SINGLE,
  children: [new TextRun({ text: "Spring 2026 · City College of New York", font: TIMES, size: BODY })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: SINGLE,
  children: [new TextRun({ text: "Final Project Report", font: TIMES, size: BODY, italics: true })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 60, after: 240, line: 240, lineRule: "auto" },
  children: [new TextRun({
    text: "Repository: github.com/ArseniiChan/canary  ·  Live demo: canary-psi.vercel.app  ·  Frozen spec tag: validation-spec-frozen",
    font: TIMES, size: SMALL,
  })],
}));

// Abstract
children.push(h1("Abstract"));
[
  "Can a computer reading the words in an annual report tell which companies turned out to be committing accounting fraud? This project tests one specific answer. I treat each Form 10-K filing's Management's Discussion and Analysis section (Item 7) as a sequence of sentences, embed every sentence with all-MiniLM-L6-v2, train a small autoencoder (384 → 128 → 32 → 128 → 384) on clean peer filings, and score each filing by mean per-sentence reconstruction error. Training is leave-one-cohort-out and time-controlled: the model only sees clean peer filings from other cohorts dated on or before each fraud's filing date. The held-out evaluation set is six historical accounting frauds — Enron (FY2000), WorldCom (FY2001), Tyco (FY2001), HealthSouth (FY2001), Valeant (FY2014), and Lehman Brothers (FY2007). The analysis specification, including exact accession numbers, was committed and git-tagged validation-spec-frozen before any validation script ran.",
  "The headline is honest about three things. First, the pre-registered design was infeasible for Enron — under the strict LOCO + time-controlled rule no eligible training data exists, because Enron's filing date precedes every peer in every other cohort. Enron is excluded from the primary results; the exclusion is a finding about pre-registration, not fraud detection. Second, of the five remaining cohorts only Lehman ranks in the top three (rank 3/13, sentence-level Mann-Whitney p ≈ 1.3 × 10⁻⁹, rank-biserial effect +0.12); the other four rank at or below random. Aggregate hit-rates are at or below the random baseline. Third, a post-hoc TF-IDF + truncated-SVD trivial baseline matches or exceeds the autoencoder on every cohort and produces a stronger Lehman signal (p ≈ 5 × 10⁻²², rank 1/13). On this dataset, the 2020s neural model adds no measurable signal beyond a 1990s latent-semantic-analysis baseline. The contribution is methodological: pre-registration that survives an uncomfortable result, plus a baseline check the field claims to want and rarely produces.",
].forEach(t => children.push(p(t, { indent: { firstLine: 360 } })));

// 1. Introduction
children.push(h1("1. Introduction and Driving Question"));
[
  "The Management's Discussion and Analysis (MD&A) section of a 10-K is the longest stretch of free-form prose in a public company's annual report — Item 7 in the standard SEC form, where management explains the year in their own words. A literature in accounting and finance argues that companies that later turn out to have been committing fraud leave detectable linguistic fingerprints in their pre-discovery filings. The natural question is whether unsupervised novelty detection — sentence embeddings plus a reconstruction-error model trained on clean filings — can recover that fingerprint without ever seeing a fraud label.",
  "I tested one such answer. The driving question is:",
].forEach(t => children.push(p(t, { indent: { firstLine: 360 } })));
children.push(new Paragraph({
  spacing: LINE, alignment: AlignmentType.CENTER,
  children: [new TextRun({
    text: "Does an unsupervised autoencoder trained on industry-and-year-matched clean 10-K MD&A text assign elevated reconstruction error to known historical fraud filings, under strictly out-of-sample evaluation?",
    font: TIMES, size: BODY, italics: true,
  })],
}));
[
  "The one-line answer this report defends: at N = 6 frauds, with a frozen pre-registered specification and strict leave-one-cohort-out plus time-controlled training, the answer is no for four of five evaluable cohorts; the one that ranks high (Lehman) is matched or exceeded by a 1990s-era TF-IDF baseline; and the sixth (Enron) cannot be evaluated under the pre-registered rules at all.",
  "Section 2 states the methodological contract that governs every downstream choice. Section 3 describes the data construction. Section 4 covers MD&A extraction. Section 5 specifies the single signal. Section 6 covers the statistical defense, including the post-hoc TF-IDF baseline that the council reviewing this work demanded. Section 7 reports per-fraud results. Section 8 collects conclusions, limitations, and future work.",
  "This is not a fraud detector. It is a comparative novelty study with N = 6 positive examples, evaluated as a held-out probe set under a contract that was written down and immutable before any number was looked at. The discipline of the contract is the deliverable; the numbers it produced are evidence the contract held.",
].forEach(t => children.push(p(t, { indent: { firstLine: 360 } })));

children.push(caption("Table 0. Mapping of project components to CSC 44800 lectures."));
children.push(buildTable(
  ["Component", "Course coverage"],
  [
    ["MiniLM sentence embeddings (the input to every model)", "AI 33 Attention and transformers; AI 35 Encoders and decoders; Meetings 22–23 (LLMs, Apr 30 / May 5)"],
    ["Custom autoencoder, 384 → 128 → 32 → 128 → 384 ReLU, MSE, Adam", "AI 27 Neural networks; AI 35 Encoders and decoders; AI 28 Tensors; AI 31 Computational graphs; AI 10 Optimizers"],
    ["Post-hoc TF-IDF + truncated-SVD baseline", "AI 12 Introduction to machine learning"],
    ["Mann-Whitney U + bootstrap + null permutation", "Adjacent — Russell & Norvig general framing of empirical evaluation"],
  ],
  [3500, 5860]
));

// 2. Methodological Contract
children.push(h1("2. The Methodological Contract"));
[
  "The plan went through two adversarial review rounds and a five-advisor council deliberation before any code ran. The output is analysis_spec.md, committed to the repository and tagged validation-spec-frozen. Once tagged, the file is immutable: scripts/06_validate.py runs once against the frozen spec and produces a single set of numbers reported as-is. The full forensic record — commit 98d2585, tag validation-spec-frozen, datestamp 2026-05-01 13:42:42 EDT — is on the repository.",
  "Three rules govern the analysis. Out-of-sample, always — leave-one-cohort-out: for each held-out fraud cohort C, the autoencoder is trained on clean peer filings from cohorts other than C, and the fraud filing in C and its peers are never in the training set. Time-controlled training: only filings dated on or before each fraud's filing date are eligible within the LOCO training set; the model cannot be informed by post-fraud disclosure language. Single pass, no tuning: architecture, hyperparameters, sentence cap, seeds, and the test set were all committed before validation, and no tuning of any of these choices took place after observing per-fraud rank numbers.",
  "A peer is admitted to a cohort iff three rules hold: the CIK is not on an editable AAER deny-list (sourced from public knowledge of SEC enforcement releases); the same CIK has filed no Form 10-K/A within five years post-filing; the CIK or company name is not on an editable class-action deny-list. Both deny-lists are committed at data/processed/aaer_denylist.txt and data/processed/classaction_denylist.txt.",
  "What this project deliberately does not do: call itself a fraud detector; train any supervised classifier on fraud labels; use Benford's Law (an early draft did; the second adversarial review pointed out Benford applies to financial-statement line items, not narrative); include foreign-issuer 20-Fs; compose multiple signals into a \"Canary score\"; claim that any fraud would have been \"flagged N months early\"; or modify the primary configuration after observing primary results.",
].forEach(t => children.push(p(t, { indent: { firstLine: 360 } })));

// 3. Data
children.push(h1("3. Data"));
children.push(p(
  "The held-out evaluation set is six 10-K filings, all pre-discovery (Table 1). Each fraud's accession was verified against a documented public revelation date before being committed to the spec.",
  { indent: { firstLine: 360 } }
));
children.push(caption("Table 1. Held-out fraud filings."));
children.push(buildTable(
  ["#", "Company", "CIK", "FY", "Filed", "SIC", "Days pre-disc."],
  [
    ["1", "Enron Corp.", "0001024401", "2000", "2001-04-02", "6200", "197"],
    ["2", "WorldCom Inc.", "0000723527", "2001", "2002-03-13", "4813", "104"],
    ["3", "Tyco International Ltd.", "0000833444", "2001", "2001-12-28", "3585", "157"],
    ["4", "HealthSouth Corp.", "0000785161", "2001", "2002-03-27", "8060", "357"],
    ["5", "Valeant Pharmaceuticals", "0000885590", "2014", "2015-02-25", "2834", "236"],
    ["6", "Lehman Brothers Holdings", "0000806085", "2007", "2008-01-29", "6211", "230"],
  ],
  [600, 1900, 1100, 500, 1200, 700, 1360]
));
[
  "Each cohort is constructed as same-SIC-2-digit and same-fiscal-year peers, screened against the operational clean rule. Final cohort sizes: Enron 12, HealthSouth 11, Tyco 12, Valeant 12, Lehman 12, WorldCom 12 clean peers. None required SIC-1-digit fallback.",
  "Two limitations of the data construction matter for interpretation. First, AAER and class-action screening were applied via editable deny-lists rather than systematic database lookups; a peer that committed undisclosed fraud could appear in a cohort, which would push the null toward zero (peers behave more like frauds) and make the test conservative. Second, EDGAR reports each company's currently-reported SIC, which may differ from its at-time-of-filing SIC. I use what EDGAR currently reports and apply it symmetrically across fraud and peer filings — the cleanest available rule but not a perfect control for sector-at-filing.",
].forEach(t => children.push(p(t, { indent: { firstLine: 360 } })));

// 4. MD&A Extraction
children.push(h1("4. MD&A Extraction"));
[
  "10-K filings span three formats relevant to this project: SGML-era plain-text (most pre-2002 filings), early HTML, and modern HTML. The parser at engine/parsing.py handles all three through a prioritized candidate list: it strips HTML when present, normalizes whitespace, and locates the most likely (start, end) boundary pair from a list led by (first Item 7 past TOC threshold, last Item 7A in document), with fallbacks for filings whose body MD&A header lacks a literal \"Item 7\" prefix (Tyco-style incorporation by reference). Candidate (Item 7, Item 7A) pairs within 1,000 characters of each other are filtered as TOC entries; bodies under 3,000 or over 400,000 characters are rejected.",
  "I committed in advance to a hard 80% extraction-success gate before proceeding. The parser hits 73 of 78 filings (93.6%) across all six cohorts. All six fraud filings parsed successfully (100%); the five failures are pre-2001-vintage peer filings with missing primary-document attachments or missing Item 7A end-anchors. No manual extraction fixes were applied — every parse is the parser's first attempt — so there is no possibility of asymmetric manual correction biasing the fraud-vs-peer comparison. Per-cohort detail is in reports/parsing_qa.md.",
].forEach(t => children.push(p(t, { indent: { firstLine: 360 } })));

// 5. The Single Signal
children.push(h1("5. The Single Signal"));
[
  "Each filing's MD&A body is sentence-tokenized using a regex-based splitter that protects common abbreviations. Sentences shorter than 20 characters or composed mostly of digits are dropped. Each remaining sentence is embedded with sentence-transformers/all-MiniLM-L6-v2 (384 dimensions); embeddings are cached on disk per (filing, model) for deterministic reproducibility.",
  "I implement a small symmetric autoencoder in PyTorch at engine/autoencoder.py: 384 → 128 → 32 → 128 → 384 with ReLU activations, MSE reconstruction loss, Adam optimizer at learning rate 1e-3, batch size 16, maximum 200 epochs with early stopping (patience 20) on a 20% validation split. The 32-dimensional bottleneck is small relative to the 384-dim input by design — a lossy bottleneck forces the model to retain training-distribution structure and reconstruct out-of-distribution sentences poorly. Random seeds for numpy, torch, and Python random are all 42.",
  "For each held-out fraud cohort C, the training corpus is constructed by replaying the spec's rule: every sentence from every clean peer filing in cohorts other than C, restricted to filings dated on or before C's fraud filing date. A per-filing sentence cap of 100 prevents long-MD&A pseudoreplication during training. The five trained autoencoders had training-set sizes of 1,477 (WCOM), 861 (TYC), 2,283 (HRC), 4,327 (VRX), and 3,367 (LEH) sentences. Section 8 examines whether the factor-of-five spread between Tyco and Valeant explains per-cohort rank ordering; it does not.",
  "At inference, each filing's MD&A is embedded the same way; the autoencoder's per-sentence reconstruction error is MSE between input and output for that sentence; the filing's score is the mean per-sentence reconstruction error. Per-filing scores for fraud and clean peers in each of the five LOCO cohorts are written to data/results/scores.csv and feed Section 6.",
].forEach(t => children.push(p(t, { indent: { firstLine: 360 } })));

// 6. Statistical Defense
children.push(h1("6. Statistical Defense"));
[
  "The frozen spec specifies four primary statistical analyses per cohort, all computed by scripts/06_validate.py. After observing primary results, council review demanded one additional analysis as a post-hoc check.",
  "Per-fraud rank within cohort with random-baseline comparison. All filings in a cohort are sorted by mean per-sentence reconstruction error descending (rank 1 = highest). Random-baseline expected rank for a cohort of size N is (N+1)/2 ≈ 6-7. Hit@k for k ∈ {1, 3, 5} is computed per cohort and aggregated.",
  "Mann-Whitney U on per-sentence error distributions. For each cohort, the one-sided Mann-Whitney U statistic is computed on the per-sentence reconstruction-error distribution of the fraud filing's sentences vs. all peer sentences. The alternative is \"fraud > peers.\" The test reports U, p-value, and rank-biserial correlation as effect size in [-1, 1]. Sentence counts feed directly into U, so the p-value scales with cohort sentence-count and must be read with the rank-biserial effect size, not in isolation.",
  "Bootstrap and null permutation. I draw 1,000 filing-level bootstrap resamples within each cohort (peers resampled with replacement, fraud held fixed) and report the empirical 95% CI on the fraud's rank. I also run 1,000 within-cohort null-permutation iterations: under H0 (fraud and peers exchangeable) randomly assign one filing as the \"fraud\" and recompute the rank; the empirical p-value is the fraction of permutations under which the random fraud's rank is at least as extreme as observed.",
  "Post-hoc TF-IDF + truncated-SVD baseline. The single most important question a sharp reviewer can ask of this work is would a 1990s baseline produce the same result? If yes, the autoencoder is decoration on this dataset. To answer it, I implemented the exact analog of the autoencoder pipeline using TF-IDF features and truncated SVD as the bottleneck instead of MiniLM embeddings and a neural autoencoder. For each cohort I built the same training corpus and fit a TF-IDF vectorizer (English stop-word removal, sublinear term-frequency, 20,000-feature cap) followed by truncated SVD with 32 components. Per-sentence reconstruction error in the TF-IDF feature space is mean((x − UU^T x)^2) per sentence, aggregated to a filing-level mean. Outputs are at data/results/scores_tfidf.csv and data/results/per_fraud_metrics_tfidf.json.",
  "Pre-committed decision rule for post-hoc analyses. Before running either post-hoc analysis, I committed to two acceptance conditions: the TF-IDF baseline is reported as headline contribution only if it (i) matches or exceeds the autoencoder on aggregate hit-rate at any k and (ii) reproduces the autoencoder's per-cohort rank ordering on the cohort with the smallest pre-registered MW p-value. The post-hoc entity-masking ablation is reported only if Lehman's rank delta is at most one position. Both conditions held; had either failed, the corresponding analysis would have moved to the appendix.",
].forEach(t => children.push(p(t, { indent: { firstLine: 360 } })));

// 7. Results
children.push(h1("7. Results"));
children.push(h2("7.1 Methodological exclusion of Enron"));
[
  "Enron's FY2000 10-K was filed 2001-04-02. The earliest filing in any other cohort is Tyco's, dated 2001-12-28 — 270 days later. Under the strict LOCO + time-controlled rule, Enron's eligible training set is empty: no autoencoder was trained, and no per-filing score, rank, Mann-Whitney result, or bootstrap CI can be reported for Enron without violating the frozen spec.",
  "This is the correct outcome of the contract, not a workaround for missing data. The honest reading is uncomfortable: the pre-registered design was infeasible for the most famous fraud in the dataset, and the design freeze did not catch the consequence. That is a finding about pre-registration, not fraud detection. It also illustrates a generalizable problem in held-out evaluation under temporal constraints — when held-out positive examples include the chronologically earliest one in the eligible universe, time-controlled training has no out-of-sample data to consume.",
].forEach(t => children.push(p(t, { indent: { firstLine: 360 } })));

children.push(h2("7.2 Per-fraud rank under the pre-registered autoencoder"));
children.push(caption("Table 2. Pre-registered autoencoder, single-pass against frozen spec."));
children.push(buildTable(
  ["Fraud", "N", "Rank", "Bootstrap 95% CI", "MW p", "Effect", "Train sents"],
  [
    ["Lehman (LEH)", "13", "3", "[1, 6]", "1.3 × 10⁻⁹", "+0.12", "3,367"],
    ["HealthSouth (HRC)", "12", "7", "[4, 10]", "1.0", "−0.17", "2,283"],
    ["Valeant (VRX)", "13", "8", "[5, 11]", "1.0", "−0.19", "4,327"],
    ["Tyco (TYC)", "13", "9", "[6, 12]", "1.0", "−0.14", "861"],
    ["WorldCom (WCOM)", "13", "12", "[10, 13]", "1.0", "−0.15", "1,477"],
  ],
  [1700, 600, 700, 1500, 1400, 900, 1100]
));
[
  "Lehman is the only cohort that ranks among the top three. The Mann-Whitney p-value of 1.3 × 10⁻⁹ on Lehman is small, but must be read alongside the effect size: rank-biserial of +0.12 (small) with 1,051 fraud sentences against 5,763 peer sentences. Sentence-level p-values scale aggressively with sentence count under fixed effect size; the rank-biserial effect is the more honest summary statistic. The other four cohorts show negative effect sizes — fraud per-sentence errors are statistically lower than peers' — meaning the autoencoder's signal on those cohorts is in the opposite of the predicted direction.",
  "Across the five LOCO cohorts, aggregate hit@1 = 0.00, hit@3 = 0.20, hit@5 = 0.20, against random-baseline 0.08 / 0.23 / 0.39. The observed hit-rates fall at or below random expectation at every threshold. Hit@3 and hit@5 correspond entirely to Lehman.",
].forEach(t => children.push(p(t, { indent: { firstLine: 360 } })));

children.push(h2("7.3 Trivial baseline matches or exceeds the autoencoder on every cohort"));
children.push(caption("Table 3. Post-hoc TF-IDF + SVD32 baseline vs autoencoder, same five cohorts."));
children.push(buildTable(
  ["Fraud", "AE rank", "TF-IDF rank", "AE MW p", "TF-IDF MW p", "AE effect", "TF-IDF effect"],
  [
    ["Lehman (LEH)", "3", "1", "1.3 × 10⁻⁹", "5.0 × 10⁻²²", "+0.12", "+0.19"],
    ["HealthSouth (HRC)", "7", "6", "1.0", "0.997", "−0.17", "−0.10"],
    ["Valeant (VRX)", "8", "8", "1.0", "1.0", "−0.19", "−0.15"],
    ["Tyco (TYC)", "9", "6", "1.0", "0.64", "−0.14", "−0.01"],
    ["WorldCom (WCOM)", "12", "12", "1.0", "1.0", "−0.15", "−0.14"],
  ],
  [1700, 800, 1000, 1300, 1300, 900, 1000]
));
children.push(image("ae_vs_tfidf_rank.png", 5.5));
children.push(caption("Figure 1. Per-fraud rank: pre-registered autoencoder vs post-hoc TF-IDF + SVD32 baseline. The trivial baseline matches the autoencoder on Valeant and WorldCom and outperforms it on Lehman, HealthSouth, and Tyco."));
[
  "The TF-IDF + SVD32 baseline matches the autoencoder on Valeant and WorldCom and outperforms it on Lehman, HealthSouth, and Tyco. On Lehman, the trivial baseline lands the fraud at rank 1 of 13 with MW p ≈ 5 × 10⁻²² and rank-biserial +0.19, both stronger than the autoencoder. Aggregate hit-rates for the trivial baseline are hit@1 = 0.20, hit@3 = 0.20, hit@5 = 0.40 — the only configuration in this study that exceeds the random baseline at any k.",
  "The interpretation requires care. The trivial baseline being competitive does not validate the autoencoder; it indicates that whatever signal exists at this dataset size is captured by sentence-level vocabulary distinctiveness alone. The signal that survives is text-distributional, not deep-learning-specific. At N = 6, on this signal, the 2020s neural model contributes nothing beyond a 1990s LSA baseline.",
].forEach(t => children.push(p(t, { indent: { firstLine: 360 } })));

children.push(h2("7.4 Lehman's positive result is robust to entity masking"));
children.push(p(
  "The post-hoc entity-masking ablation tests whether MiniLM's web-pretraining seeded Lehman's rank by memorizing literal mentions of \"Lehman,\" \"Fuld,\" \"Repo 105,\" or auditor names. For each cohort that has an autoencoder I hard-coded a per-cohort entity list (company name, key executives, auditor of record), replaced every case-insensitive whole-word match with [ENTITY] in the parsed MD&A, re-encoded, and rescored against the existing cohort autoencoder.",
  { indent: { firstLine: 360 } }
));
children.push(caption("Table 4. Post-hoc entity-masking on the five LOCO cohorts."));
children.push(buildTable(
  ["Cohort", "Replacements", "Original rank", "Masked rank", "Δ"],
  [
    ["LEH",  "93",  "3 / 13",  "3 / 13",  "0"],
    ["HRC",  "6",   "7 / 12",  "7 / 12",  "0"],
    ["TYC",  "93",  "9 / 13",  "11 / 13", "+2"],
    ["VRX",  "31",  "8 / 13",  "9 / 13",  "+1"],
    ["WCOM", "267", "12 / 13", "12 / 13", "0"],
  ],
  [1300, 1700, 1700, 1700, 1000]
));
children.push(p(
  "Lehman's rank is invariant under masking 93 mentions, the literal-name-leakage hypothesis fails. The matching 93-replacement totals for LEH and TYC are coincidental: LEH = 64 \"Lehman\" + 29 \"Lehman Brothers\"; TYC = 87 \"Tyco\" + 6 \"ADT\". Topical leakage (post-2008 commentary on repo accounting or off-balance-sheet vehicles) remains disclosed but unaddressed empirically.",
  { indent: { firstLine: 360 } }
));

children.push(h2("7.5 Leave-one-fraud-out + interpretation"));
children.push(p(
  "Removing each fraud in turn does not produce a regime under which the four-fraud aggregate beats random; removing Lehman drops hit@3 and hit@5 to 0.00. The aggregate result is entirely Lehman. Two readings are consistent with the data — either the single signal has no out-of-sample power at N = 6, or MD&A language is too heterogeneous for a single autoencoder reconstruction-error signal to discriminate fraud from clean peers without supervision. Both yield the same conclusion: at this dataset size, on this signal, the answer to the driving question is no.",
  { indent: { firstLine: 360 } }
));

// 8. Conclusions
children.push(h1("8. Conclusions, Limitations, Future Work"));
children.push(p("Three substantive findings emerged.", { indent: { firstLine: 360 } }));
[
  "First, a pre-registered single-signal unsupervised novelty study on SEC 10-K MD&A text, evaluated under strict LOCO + time-controlled training against six historical fraud filings, produces a negative result. Of five evaluable cohorts, four rank fraud filings at or below the random-baseline expectation. The single positive cohort (Lehman) is matched or exceeded by a 1990s-era TF-IDF + truncated-SVD trivial baseline.",
  "Second, the pre-registered design was infeasible for Enron under LOCO + time-controlled training because the chronologically earliest held-out positive has no eligible training data. That is a finding about pre-registration discipline, not fraud-detection capability — and a generalizable lesson: any held-out evaluation under temporal constraints must verify that every held-out positive admits at least one eligible training cohort under the proposed rule before the spec is frozen.",
  "Third, the trivial-baseline gap is the most decisive result. Without it, the project would have reported \"Lehman is detectable\" as the clean positive. With it, the honest claim is \"Lehman is detectable by both methods, and the more expensive method does not beat the cheaper one.\" The lesson is that a sharp baseline is not optional; a result that does not survive a baseline check is not a result.",
  "Three lessons follow. Pre-registration is load-bearing only if it survives contact with the data — the frozen spec held; I did not iterate the autoencoder, redefine \"clean,\" or retreat from Enron's exclusion. Methodological exclusions are content if owned — Section 7.1 reports Enron's exclusion as a finding rather than a workaround. The Lehman training-size confound is real, partially refuted, and named — Valeant trained on more sentences (4,327) than Lehman (3,367) and ranks 8/13, so size alone does not explain Lehman's rank; the TF-IDF baseline reproduces the Lehman-specific result, weakly arguing for a real text-distributional Lehman signature rather than a method-specific artifact.",
  "Limitations. N = 6 (effective N = 5) is too small for confidence intervals to constrain anything tightly. MiniLM pretraining contamination beyond literal-name leakage was not addressed empirically. SIC-2-digit + same-fiscal-year peer matching is coarse and admits residual heterogeneity. EDGAR's currently-reported SIC differs in some cases from the firm's at-time-of-filing SIC. The operational \"clean\" rule is editable-deny-list-only with partial coverage. The autoencoder bottleneck dimension was frozen at 32 without a sensitivity sweep.",
  "Future work. The most informative single direction is change-detection within firm: instead of comparing a fraud filing's MD&A against industry peers, compare it against the same firm's prior-year MD&A. This controls for firm-specific style at the cost of losing the fraud-vs-clean comparison and converts the question from \"is this filing anomalous against peers\" to \"is this filing anomalous against itself.\" Other directions: multi-section integration (Item 1A risk factors, Item 8 financial notes); structured-plus-unstructured fusion; a genuinely larger held-out set conditioned on AAER-confirmed fraud rather than the high-profile six; a supervised classical-ML baseline (logistic regression on TF-IDF features) once a larger fraud-label set is available — that would violate this study's contract but is the obvious follow-up.",
].forEach(t => children.push(p(t, { indent: { firstLine: 360 } })));

// References
children.push(h1("References"));
[
  "Russell, S., & Norvig, P. (2020). Artificial Intelligence: A Modern Approach (4th ed.). Pearson.",
  "Burden, R. L., & Faires, J. D. (2010). Numerical Analysis (9th ed.). Brooks/Cole.",
  "Cecchini, M., Aytug, H., Koehler, G. J., & Pathak, P. (2010). Making words work: Using financial text as a predictor of financial events. Decision Support Systems, 50(1), 164–175.",
  "Loughran, T., & McDonald, B. (2011). When is a liability not a liability? Textual analysis, dictionaries, and 10-Ks. The Journal of Finance, 66(1), 35–65.",
  "Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. Proc. EMNLP-IJCNLP 2019.",
  "U.S. Securities and Exchange Commission. EDGAR full-text search and submissions JSON. https://www.sec.gov/edgar.",
  "U.S. Securities and Exchange Commission. Accounting and Auditing Enforcement Releases. https://www.sec.gov/divisions/enforce/friactions.shtml.",
  "Project repository: https://github.com/ArseniiChan/canary. All code, frozen spec, deny-lists, parsed MD&A index, training logs, single-pass validation outputs, post-hoc baseline outputs, figures, and the appendices (cohort overview, parsing QA, model inventory, training-quality diagnostics) are committed to the repo. Live demo: https://canary-psi.vercel.app.",
].forEach(t => children.push(new Paragraph({
  children: [new TextRun({ text: t, font: TIMES, size: BODY })],
  spacing: { ...LINE, before: 80 }, indent: { left: 360, hanging: 360 },
})));

// ---- APPENDICES (do not count toward body page limit per syllabus) ----

children.push(h1("Appendix A — Frozen analysis spec"));
children.push(p(
  "Committed at analysis_spec.md in the project repository, git-tagged validation-spec-frozen at commit 98d2585 on 2026-05-01 13:42:42 EDT before any validation script ran. Contains exact accession numbers for all six fraud filings, verified pre-discovery dates and sources, and the full primary-configuration block (architecture, optimizer, seeds, sentence cap, statistical methods, peer-matching rule, and operational \"clean\" definition).",
  { indent: { firstLine: 360 } }
));

children.push(h1("Appendix B — Cohort overview"));
children.push(p(
  "Per-cohort peer lists, clean-rule outcomes per peer, and SIC-distribution within each cohort are in reports/cohort_overview.md. The five trained autoencoders had training-set sizes: WCOM 1,477 sentences from 19 filings; TYC 861 from 11; HRC 2,283 from 29; VRX 4,327 from 55; LEH 3,367 from 43.",
  { indent: { firstLine: 360 } }
));

children.push(h1("Appendix C — Parsing QA"));
children.push(p(
  "Extraction success rate by fraud-vs-peer status and by year, per-filing parse method and character/sentence counts, and the failure list are in reports/parsing_qa.md. Total: 73/78 filings successfully extracted (93.6%); fraud filings: 6/6 (100%); five failures all in pre-2001-vintage peer filings with missing primary documents or missing Item 7A end-anchors.",
  { indent: { firstLine: 360 } }
));

children.push(h1("Appendix D — Post-hoc analyses (script paths)"));
children.push(p(
  "TF-IDF + SVD32 trivial baseline: scripts/09_tfidf_baseline.py; outputs at data/results/scores_tfidf.csv and data/results/per_fraud_metrics_tfidf.json. Entity-masking ablation: scripts/10_entity_masking_posthoc.py; output at data/results/entity_masking_posthoc.json. Both clearly labeled post-hoc and exploratory; neither displaces the primary numbers in data/results/per_fraud_metrics.json.",
  { indent: { firstLine: 360 } }
));

children.push(h1("Appendix E — Reproducibility"));
children.push(new Paragraph({
  spacing: SINGLE,
  children: [new TextRun({
    font: "Consolas", size: SMALL,
    text: "make install                                          # one-time\nmake pin-accessions                                   # Phase 0; commits + tags spec\nmake reproduce                                        # full pipeline through figures\nmake test                                             # 36 unit tests\n.venv/bin/python scripts/09_tfidf_baseline.py         # post-hoc baseline\n.venv/bin/python scripts/10_entity_masking_posthoc.py # post-hoc masking\n.venv/bin/python scripts/14_training_quality_diagnostics.py  # Appendix G figures",
  })],
}));
children.push(p(
  "Random seeds for numpy, torch, and Python random are fixed at 42. Embeddings are cached on disk per (filing, model). Every figure in reports/figures/ regenerates from data/results/.",
  { indent: { firstLine: 360 } }
));

children.push(h1("Appendix F — Model inventory"));
children.push(p(
  "The Canary project uses three distinct kinds of model, totalling eleven model instances:",
  { indent: { firstLine: 360 } }
));
[
  "(F.1) Pretrained transformer — used as a frozen feature extractor. sentence-transformers/all-MiniLM-L6-v2, a 6-layer MiniLM-based transformer pretrained by Microsoft Research and the Hugging Face Sentence-Transformers project on more than one billion sentence pairs. Approximately 22M parameters. Outputs 384-dimensional sentence vectors. We do not train this model — we freeze it and use it as the input encoder for every MD&A sentence in the project.",
  "(F.2) Custom autoencoders — the models trained for this project. Five PyTorch autoencoders, one per cohort (HRC, LEH, TYC, VRX, WCOM), with architecture 384 → 128 → 32 → 128 → 384 and ReLU activations between layers. Approximately 117,000 parameters each. MSE reconstruction loss; Adam at learning rate 1e-3; batch size 16; maximum 200 epochs with early stopping (patience 20) on a 20% validation split; numpy / torch / Python random seeds all 42. Trained from scratch on each cohort's leave-one-cohort-out and time-controlled training corpus. Saved checkpoints at data/processed/models/<TICKER>.pt reload cleanly and reproduce the committed per-cohort fraud scores to six decimal places (verified at the validation freeze and re-verified before the May 7 presentation).",
  "(F.3) Classical-ML baseline — post-hoc, council-mandated. Five TF-IDF + TruncatedSVD pipelines, one per cohort, trained on the same LOCO + time-controlled training corpora. TF-IDF vectorizer with English stop-word removal, sublinear term-frequency scaling, and a 20,000-feature cap; TruncatedSVD with 32 components — matching the autoencoder bottleneck dimension exactly so the comparison is apples-to-apples on bottleneck capacity.",
].forEach(t => children.push(p(t, { indent: { firstLine: 360 } })));

children.push(h1("Appendix G — Training-quality diagnostics"));
children.push(p(
  "Three diagnostics, all from scripts/14_training_quality_diagnostics.py, prove that the autoencoders trained for this project are real working models, not artifacts that merely compiled.",
  { indent: { firstLine: 360 } }
));

children.push(h2("G.1 Per-epoch convergence"));
children.push(p(
  "Each of the five cohort autoencoders converged via early stopping at best epoch 50–59 of a 200-epoch maximum, with patience 20. Final train loss ranged from 0.000736 (HRC) to 0.000911 (VRX); final validation loss from 0.000947 (HRC) to 0.001129 (TYC). The train-validation gap was small everywhere — between 0.000111 (VRX, largest training set) and 0.000301 (TYC, smallest training set). Full training log: data/processed/training_log.json.",
  { indent: { firstLine: 360 } }
));

children.push(h2("G.2 Noise sanity check"));
children.push(p(
  "The decisive test that the autoencoder learned a meaningful manifold rather than a trivial constant function. For each cohort autoencoder, I scored four kinds of input under the same per-sentence MSE reconstruction-error metric: (i) the cohort's clean-peer sentences, (ii) the cohort's fraud-filing sentences, (iii) 1,000 unit-norm Gaussian vectors of the same dimensionality, and (iv) 1,000 raw N(0, 1) vectors.",
  { indent: { firstLine: 360 } }
));
children.push(caption("Table G.1. Mean per-sentence reconstruction error by input type."));
children.push(buildTable(
  ["Cohort", "Real peer", "Real fraud", "Unit-norm Gaussian", "Raw N(0,1)", "Noise / real ratio"],
  [
    ["HRC",  "0.001406", "0.001266", "0.002954", "1.076235", "2.1× / 765×"],
    ["LEH",  "0.001337", "0.001395", "0.002966", "1.077481", "2.2× / 806×"],
    ["TYC",  "0.001362", "0.001271", "0.002891", "1.022643", "2.1× / 751×"],
    ["VRX",  "0.001442", "0.001295", "0.002896", "1.103497", "2.0× / 765×"],
    ["WCOM", "0.001375", "0.001259", "0.002858", "1.041342", "2.1× / 760×"],
  ],
  [1100, 1300, 1400, 1900, 1500, 2160]
));
children.push(p(
  "Out-of-distribution input — Gaussian noise — produces reconstruction error 2× higher (matched magnitude) and roughly 750× higher (raw white noise) than real MD&A sentences. The autoencoders demonstrably learned the structure of MiniLM-encoded MD&A text.",
  { indent: { firstLine: 360 } }
));

children.push(h2("G.3 The painful gap that explains the negative result"));
children.push(p(
  "Table G.1 also makes the negative result visible: real fraud and real peer sentences differ by roughly 10% in mean reconstruction error (around 0.0013 vs around 0.0014), whereas real text and matched-magnitude Gaussian noise differ by approximately 100% (around 0.0014 vs around 0.0029). The model can clearly distinguish MD&A text from non-text; it cannot reliably distinguish fraud-filing MD&A from clean-peer MD&A. That gap is the substantive finding of the project. The autoencoders are real, working, and well-trained models in the technical sense — they reconstruct in-distribution input two orders of magnitude better than out-of-distribution input. They are not, however, useful detectors of accounting fraud at this dataset size on this signal.",
  { indent: { firstLine: 360 } }
));

// Build & save
const doc = new Document({
  styles: {
    default: { document: { run: { font: TIMES, size: BODY } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: H1, bold: true, font: TIMES },
        paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: H2, bold: true, font: TIMES },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 1 } },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "Canary — Arsenii Chan — CSC 44800 — Page ", font: TIMES, size: SMALL }),
            new TextRun({ children: [PageNumber.CURRENT], font: TIMES, size: SMALL }),
          ],
        })],
      }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log(`wrote ${OUT}  (${buf.length.toLocaleString()} bytes)`);
});
