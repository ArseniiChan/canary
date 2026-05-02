# Canary — A Pre-Registered Single-Signal Novelty Study on SEC 10-K MD&A Text

**Course:** CSC 44800 — Artificial Intelligence (CCNY, Spring 2026)
**Author:** Arsenii Chan
**Advisor:** Prof. Erik K. Grimmelmann
**Repository:** https://github.com/ArseniiChan/canary
**Frozen analysis spec:** [analysis_spec.md](../analysis_spec.md) (git tag `validation-spec-frozen`, committed 2026-05-01 before any validation ran)

---

## Abstract

Can a computer reading the words in an annual report tell which companies turned out to be committing accounting fraud? This project tests one specific answer to that question. I treat each Form 10-K filing's Management's Discussion and Analysis section (Item 7) as a sequence of sentences, embed every sentence with the `all-MiniLM-L6-v2` sentence-transformer, train a small autoencoder (384 → 128 → 32 → 128 → 384) on clean peer filings, and score each filing by the mean per-sentence reconstruction error. The training regime is leave-one-cohort-out and time-controlled: for each held-out fraud cohort, the autoencoder only sees clean peer filings from *other* cohorts dated on or before that fraud's filing date. The held-out evaluation set is six historical accounting frauds — Enron (FY2000), WorldCom (FY2001), Tyco (FY2001), HealthSouth (FY2001), Valeant (FY2014), and Lehman Brothers (FY2007) — paired with industry-and-year-matched peer cohorts. The analysis specification, including exact accession numbers, was committed to the repository and git-tagged `validation-spec-frozen` before any validation script ran.

The headline is honest about three things at once. First, the pre-registered design was infeasible for Enron: under the strict leave-one-cohort-out plus time-controlled rule, no eligible training data existed for Enron's cohort, because Enron's filing date precedes every peer filing in every other cohort. Enron is excluded from the primary results; that exclusion is a finding about pre-registration, not about fraud detection. Second, of the five remaining cohorts, only Lehman Brothers ranks in the top three within its peer cohort (rank 3 of 13, sentence-level Mann-Whitney *p* ≈ 1.3 × 10⁻⁹, rank-biserial effect size +0.12). The other four cohorts (HealthSouth 7/12, Tyco 9/13, Valeant 8/13, WorldCom 12/13) rank at or below the random-baseline expectation. Aggregate hit-rates are hit@1 = 0.00, hit@3 = 0.20, hit@5 = 0.20 — at or below the random baseline of 0.08, 0.23, 0.39. Third, a post-hoc TF-IDF + truncated-SVD trivial baseline, run on the same training corpora and the same five cohorts, matches or exceeds the autoencoder on every cohort and produces an even stronger Mann-Whitney signal on Lehman (*p* ≈ 5 × 10⁻²², rank 1 of 13). At this dataset size and on this signal, the 2020s neural model adds nothing beyond a 1990s latent-semantic-analysis baseline.

The discipline that makes this finding informative is the discipline that costs nothing to replicate: pre-register the spec, freeze it, leave one cohort out, control for filing time, and report the single-pass numbers. The contribution is methodological, not detective.

## 1. Introduction and Driving Question

When an investor reads a public company's 10-K, the longest stretch of free-form prose is the Management's Discussion and Analysis section — Item 7 in the standard SEC form. That section is where management explains the year in their own words. A long literature in accounting and finance has examined whether the language in MD&A leaks information that the financial statements do not, including whether companies that later turn out to have been committing fraud leave a detectable linguistic fingerprint in their pre-discovery filings. The natural question that follows is whether modern unsupervised novelty detection — sentence embeddings plus a reconstruction-error model trained on clean filings — can recover that fingerprint without ever seeing a fraud label during training.

I tested one such answer. The driving question is:

> *Does an unsupervised autoencoder trained on industry-and-year-matched clean 10-K MD&A text assign elevated reconstruction error to known historical fraud filings, under strictly out-of-sample evaluation?*

The one-line answer this report defends: **at N = 6 frauds, with a frozen pre-registered specification and strict leave-one-cohort-out plus time-controlled training, the answer is no for four of five evaluable cohorts; the one cohort that ranks high (Lehman Brothers) is matched or exceeded by a 1990s-era TF-IDF baseline, and the sixth cohort (Enron) cannot be evaluated under the pre-registered rules at all.**

This report is organized accordingly. Section 2 states the methodological contract that governs every downstream choice, including the things this project deliberately does not do. Section 3 describes the data construction — the six fraud filings, the SIC-2-digit cohort matching, the operational definition of "clean," and the limitations of each. Section 4 describes the MD&A extraction pipeline and reports the parsing-quality gate. Section 5 describes the single signal — sentence embeddings, the autoencoder architecture, and the leave-one-cohort-out plus time-controlled training rule. Section 6 covers the statistical defense: Mann-Whitney U, bootstrap confidence intervals, null permutation, and a post-hoc TF-IDF + truncated-SVD trivial baseline that the council judging this work demanded I include. Section 7 reports the per-fraud results and the post-hoc entity-masking ablation. Section 8 collects the conclusions, the limitations the data could not address, and the future-work direction that survives this study.

A note on framing. This is **not** a fraud detector and the report does not call it one. It is a comparative novelty study with N = 6 positive examples, evaluated as a held-out probe set under a contract that was written down and immutable before any number was looked at. The discipline of that contract is the deliverable; the numbers it produced are evidence the contract held.

**Course-content mapping.** The components of this project map to the CSC 44800 lecture sequence as follows: the autoencoder (Section 5) implements *AI 27 Neural networks* and *AI 35 Encoders and decoders* — an autoencoder is literally an encoder-decoder pair trained to reconstruct its input through a low-dimensional bottleneck. The PyTorch implementation uses concepts from *AI 28 Tensors*, *AI 31 Computational graphs*, and *AI 10 Optimizers* (Adam). The MiniLM sentence embeddings (Section 5) use a pretrained encoder built on the architecture taught in *AI 33 Attention and transformers* and the encoder side of *AI 35*. The post-hoc TF-IDF + truncated-SVD baseline (Section 6.4) is a classical pre-neural feature pipeline, motivated by *AI 12 Introduction to machine learning* — included specifically to test whether the neural model earns its complexity. Statistical methodology (Section 6) is adjacent to course material rather than a specific lecture; the bootstrap, null-permutation, and Mann-Whitney U procedures follow Russell & Norvig's general treatment of empirical evaluation. The project deliberately does not use search (AI 8–9), reinforcement learning (AI 11), the perceptron/SVM/decision-tree/boosting/random-forest sequence (AI 14–25), CNNs (AI 30), or RNNs (AI 32) — those are the bulk of the curriculum, and a future generalization of this study should compare the autoencoder against at least one supervised classical-ML baseline (logistic regression on TF-IDF features is the obvious candidate); the present study deliberately avoids supervised training on fraud labels (Section 2), so a supervised baseline would require relaxing the contract.

## 2. The Methodological Contract

The plan for this project went through two adversarial review rounds and a five-advisor council deliberation before any code ran. The output of those deliberations is `analysis_spec.md`, which is committed to the project repository and tagged `validation-spec-frozen`. Once tagged, the file is immutable: the validation script (`scripts/06_validate.py`) runs once against that frozen spec, produces a single set of numbers, and those numbers are reported as-is. Whatever the numbers say, that is the result.

**No supervised training on fraud labels.** The six historical frauds are a held-out evaluation set used once for the primary precision-at-rank reporting. Ablations are descriptive and live in the appendix only — they never select or defend the primary result.

**Out-of-sample scoring, always — leave-one-cohort-out.** For each held-out fraud cohort C, the autoencoder is trained on clean peer filings from cohorts other than C. The fraud filing in C and its peers are never in the training set for C's autoencoder. Without this rule, peer filings would be in-sample to a model evaluated on them and would carry a structural reconstruction-error advantage, invalidating the test. This was the central correction in the second adversarial review round before the spec was frozen.

**Time-controlled training.** Within the leave-one-cohort-out training set, only filings dated on or before each fraud's filing date are eligible. The model's representation of "clean" cannot be contaminated by post-fraud disclosure language.

**Pre-discovery filings only.** Each fraud's accession number was verified against a documented public revelation date before being committed to the spec; the verification table lives in Section 7 of `analysis_spec.md`. None of the six 10-Ks were filed after the corresponding fraud was disclosed publicly.

**Industry- and year-matched peers.** Each cohort is constructed as same-SIC-2-digit and same-fiscal-year peers of the fraud. SIC-1-digit fallback was permitted only when SIC-2-digit yielded fewer than six clean peers, and any fallback cohort would have been reported separately and excluded from primary results. None of the six final cohorts required the fallback.

**"Clean" defined operationally.** A peer is admitted to a cohort iff it satisfies three rules: (i) the CIK is not on an editable AAER deny-list sourced from public knowledge of SEC enforcement releases; (ii) the same CIK has filed no Form 10-K/A within five years post-filing; (iii) the CIK or company name is not on an editable class-action deny-list sourced from public knowledge of major settlements. Both deny-lists are committed to the repository at `data/processed/aaer_denylist.txt` and `data/processed/classaction_denylist.txt`.

**Frozen primary configuration.** The architecture (384 → 128 → 32 → 128 → 384, ReLU, MSE, Adam learning rate 1e-3, 200 epochs with early stopping on a 20% validation split, all seeded), the per-filing sentence cap of 100 during training, and the choice of mean per-sentence reconstruction error as the primary aggregation are all committed to the spec before validation. No tuning of any of these choices took place after observing per-fraud rank numbers.

**What this project deliberately does not do.** It does not call itself a fraud detector anywhere. It does not train any supervised classifier on the historical fraud labels. It does not use Benford's Law (the original draft of this plan did; the second adversarial review pointed out that Benford's Law applies to financial-statement line items, not free-text discussion, and it was removed from the spec before code was written). It does not include foreign-issuer 20-F filings such as Luckin Coffee, since those are incompatible with a 10-K Item 7 methodology. It does not compose multiple signals into a "Canary score." It does not claim that any of the six frauds would have been "flagged N months early." And it does not, under any condition, modify the primary configuration after observing primary results.

## 3. Data

The held-out evaluation set is six 10-K filings, all pre-discovery. The SEC EDGAR accession numbers, filing dates, and verification details are committed to `analysis_spec.md` under git tag `validation-spec-frozen`.

**Table 1. Held-out fraud filings.**

| # | Company | CIK | FY | Accession | Filed | Period | SIC | Days pre-discovery |
|---|---|---|---|---|---|---|---|---:|
| 1 | Enron Corp. | 0001024401 | 2000 | `0001024401-01-500010` | 2001-04-02 | 2000-12-31 | 6200 | 197 |
| 2 | WorldCom Inc. | 0000723527 | 2001 | `0001005477-02-001226` | 2002-03-13 | 2001-12-31 | 4813 | 104 |
| 3 | Tyco International Ltd. | 0000833444 | 2001 | `0000912057-01-544874` | 2001-12-28 | 2001-09-30 | 3585 | 157 |
| 4 | HealthSouth Corp. | 0000785161 | 2001 | `0001005150-02-000448` | 2002-03-27 | 2001-12-31 | 8060 | 357 |
| 5 | Valeant Pharmaceuticals | 0000885590 | 2014 | `0000885590-15-000015` | 2015-02-25 | 2014-12-31 | 2834 | 236 |
| 6 | Lehman Brothers Holdings | 0000806085 | 2007 | `0001104659-08-005476` | 2008-01-29 | 2007-11-30 | 6211 | 230 |

Public revelation dates and sources for each are documented in `analysis_spec.md`. The shortest pre-discovery window was WorldCom at 104 days; the longest was HealthSouth at 357 days.

**Cohort construction.** For each fraud, I pulled the SIC-2-digit code from EDGAR's currently-reported submissions JSON and assembled the candidate cohort as every 10-K filed by a company with the same SIC-2-digit and the same fiscal-year period of report. Each candidate was screened against the operational clean rule. Final cohort sizes after clean-screening: Enron 12 peers, HealthSouth 11, Tyco 12, Valeant 12, Lehman 12, WorldCom 12. None of the six required the SIC-1-digit fallback.

**Limitation of "clean" as defined here.** AAER and class-action screening were applied via editable deny-lists rather than systematic database lookups. A peer that committed undisclosed fraud could appear in a cohort. Empirically, this would push the null toward zero (peers behave more like frauds), making the test conservative — but the disclosure belongs in this section, not buried in a footnote. The specific peers admitted to each cohort are listed in `reports/cohort_overview.md`.

**Limitation of currently-reported SIC.** EDGAR reports each company's currently-reported SIC code, which is not necessarily the SIC code in effect at the time of the filing. Enron is currently classified as SIC 6200 (Security & Commodity Brokers), not as a 1300-series energy classification. I use what EDGAR currently reports and apply it symmetrically across fraud and peer filings, which is the cleanest available rule but does not perfectly control for sector at the time of filing.

## 4. MD&A Extraction

10-K filings on EDGAR span three formats relevant to this project: SGML-era plain-text submissions (Enron, WorldCom, Tyco, HealthSouth and most of their peers), early HTML (some 2001-vintage peers), and modern HTML (Valeant, Lehman, and their peers). The parser at `engine/parsing.py` handles all three.

The extraction strategy is a prioritized candidate list. For each filing, the parser strips HTML when present, normalizes whitespace, and locates the most likely (start, end) boundary pair from a list that includes (first Item 7 past TOC threshold, last Item 7A in document) as the canonical pair, with fallbacks including a "Management's Discussion and Analysis" body anchor for filings whose body MD&A header lacks the literal "Item 7" prefix (Tyco-style incorporation by reference). Candidate (Item 7, Item 7A) pairs that appear within 1000 characters of each other are filtered out as TOC entries rather than real body headers. Bodies that are unrealistically short (< 3,000 characters) or unrealistically long (> 400,000 characters) are rejected.

I committed in advance to a hard 80% extraction-success gate before proceeding to embeddings; the parser hits **73 of 78 filings successfully extracted, or 93.6%** across the six cohorts. The QA pipeline at `reports/parsing_qa.md` reports success rate by fraud-vs-peer status and by year. Notably, all six fraud filings parsed successfully (100%); the five failures were all in pre-2001-vintage peer filings and involved either missing primary-document attachments on EDGAR or missing Item 7A end-anchors. I did not apply any manual extraction fixes — every per-filing parse is the parser's first attempt — so there is no possibility of asymmetric manual correction biasing the fraud-vs-peer comparison.

**The pre-2001 cohort warning.** Enron's cohort had the lowest extraction success rate at 69.2%; HRC, TYC, VRX, and LEH all came in above 90%. The Enron-cohort extraction shortfall is one of two structural problems with that cohort, the other being the absence of any LOCO + time-controlled training data; together they motivate Enron's exclusion from primary results, treated as a finding in Section 7.

## 5. The Single Signal

Each filing's MD&A body is sentence-tokenized using a regex-based splitter that protects common abbreviations. Sentences shorter than 20 characters or composed mostly of digits are dropped. Each remaining sentence is embedded with `sentence-transformers/all-MiniLM-L6-v2`, producing a 384-dimensional vector. The embeddings are cached on disk per (filing, model) so that the pipeline reproduces deterministically.

**The autoencoder.** I implement a small symmetric autoencoder in PyTorch at `engine/autoencoder.py`: 384 → 128 → 32 → 128 → 384, ReLU activations between layers, MSE reconstruction loss. Optimizer is Adam at learning rate 1e-3, batch size 16, 200 epochs with early stopping on a 20% validation split (patience 20 epochs). The bottleneck dimension of 32 is small relative to 384 by design — a lossy bottleneck forces the model to retain the structure of the training distribution and reconstruct out-of-distribution sentences poorly. Random seeds for `numpy`, `torch`, and Python's `random` are all 42.

**Leave-one-cohort-out plus time-controlled training.** For each held-out fraud cohort C, the training corpus is constructed by replaying the spec's rule: every sentence from every clean peer filing in cohorts other than C, restricted to filings dated on or before C's fraud filing date. A per-filing sentence cap of 100 prevents long-MD&A pseudoreplication during training; if a filing has more than 100 sentences, 100 are uniformly sampled. The five trained autoencoders that resulted (Enron's was infeasible — Section 7) had training-set sizes of 1,477 sentences (WCOM), 861 (TYC), 2,283 (HRC), 4,327 (VRX), and 3,367 (LEH). The factor-of-five spread between Tyco's training set and Valeant's is a real asymmetry; Section 8 examines whether it explains the per-cohort rank ordering and concludes that it does not.

**Filing-level scoring.** At inference, each filing's MD&A is sentence-tokenized and embedded the same way; the autoencoder's per-sentence reconstruction error is computed as MSE between input and output for that sentence; and the filing's score is the mean per-sentence reconstruction error. Trimmed-mean (5%) and max are computed and reported as descriptive ablations only — they never enter the primary result.

The per-filing scores for fraud and clean peers in each of the five LOCO cohorts are written to `data/results/scores.csv` and form the primary input to the statistical defense in Section 6.

## 6. Statistical Defense

The frozen spec specifies four primary statistical analyses per cohort plus a leave-one-fraud-out aggregate sensitivity, all computed by `scripts/06_validate.py` against `analysis_spec.md`. After observing the primary results, the council reviewing this work demanded one additional analysis as a post-hoc check: a TF-IDF + truncated-SVD trivial baseline. Section 6.4 reports the post-hoc baseline; Section 6.5 reports the post-hoc entity-masking ablation. Both are clearly labeled as post-hoc and exploratory; they do not displace the pre-registered primary numbers.

### 6.1 Per-fraud rank with random-baseline comparison

For each cohort, I sort all filings by their mean per-sentence reconstruction error (descending — rank 1 is the most "novel" / highest reconstruction error) and report the fraud's rank within the cohort, paired with the random-baseline expected value. Hit@k is computed for k = 1, 3, 5 per cohort and aggregated across cohorts.

### 6.2 Mann-Whitney U on per-sentence error distributions

Within each cohort I compute the one-sided Mann-Whitney U statistic on the per-sentence reconstruction-error distribution of the fraud filing's sentences against the concatenated per-sentence error distribution of all clean peers' sentences in the cohort. The alternative hypothesis is "fraud > peers." The test reports the U statistic, the p-value, and the rank-biserial correlation as effect size in [-1, 1], where positive values mean fraud sentences tend to have higher reconstruction error than peer sentences. Sentence counts feed directly into U, so the p-value scales with cohort sentence-count and must be read with the rank-biserial effect size, not in isolation. Reporting both is non-negotiable — Section 7 does so.

### 6.3 Bootstrap CIs and null permutation

I draw 1,000 filing-level bootstrap resamples within each cohort (peers resampled with replacement, fraud held fixed) and report the empirical 95% CI on the fraud's rank. I also run 1,000 within-cohort null-permutation iterations: under the null hypothesis that fraud and peers are exchangeable, randomly assign one filing as the "fraud" and recompute the rank; the empirical p-value reported is the fraction of permutations under which the random fraud's rank is at least as extreme as the observed rank. Both procedures are seeded.

### 6.4 Post-hoc TF-IDF + truncated-SVD trivial baseline

The single most important question a sharp reviewer can ask of this work is: *would a 1990s baseline produce the same answer?* If yes, the autoencoder is decoration on this dataset. To answer it, I implemented the exact analog of the autoencoder pipeline using TF-IDF features and truncated SVD as the bottleneck instead of MiniLM embeddings and a neural autoencoder, and ran it on the same five LOCO + time-controlled training corpora. The script is `scripts/09_tfidf_baseline.py`.

For each cohort C, I built the same training corpus the autoencoder saw and fit a TF-IDF vectorizer with English stop-word removal, sublinear term-frequency scaling, and a 20,000-feature cap, followed by truncated SVD with 32 components — the same bottleneck dimension as the autoencoder. I compute the per-sentence reconstruction error in the TF-IDF feature space as `mean((x - U U^T x)^2)` per sentence, then aggregate to a filing-level mean. The Mann-Whitney, bootstrap, null-permutation, and rank computations are identical to the autoencoder pipeline.

The outputs are at `data/results/scores_tfidf.csv` and `data/results/per_fraud_metrics_tfidf.json`. Section 7 reports the head-to-head against the autoencoder. The summary is that the trivial baseline matches or exceeds the autoencoder on every cohort and produces a stronger Mann-Whitney signal on Lehman.

### 6.5 Post-hoc entity-masking ablation

The pre-registered ablation targeted Enron alone, motivated by the concern that MiniLM's web-pretrained embeddings might leak information about specific famous fraud cases via literal-name tokens ("Enron", "Skilling", "Andersen"). When the LOCO + time-controlled rule made Enron's primary result infeasible, the ablation as pre-registered also became infeasible — Enron has no autoencoder of its own to score against. Rather than relax the spec, I dropped the pre-registered ablation entirely and replaced it with a post-hoc analog, clearly labeled.

The post-hoc ablation, at `scripts/10_entity_masking_posthoc.py`, runs on the five cohorts that *do* have autoencoders: HRC, LEH, TYC, VRX, WCOM. For each, I hard-coded a small per-cohort entity list including the company name, key executives named in subsequent SEC filings, and the auditor of record; replaced every case-insensitive whole-word match with the literal token `[ENTITY]` in the parsed MD&A; re-encoded the masked text with MiniLM; scored against the existing cohort autoencoder; and recomputed the fraud's rank. The number of replacements ranged from 6 (HRC) to 267 (WCOM). Output is `data/results/entity_masking_posthoc.json`. Section 7 reports the rank deltas.

### 6.6 Pre-committed decision rule for the post-hoc TF-IDF baseline

The pre-registered analysis specification covered the autoencoder. The TF-IDF + truncated-SVD baseline in §6.4 and the entity-masking ablation in §6.5 were both added after the autoencoder primary results were observed. To keep the post-hoc analyses from sliding into hypothesizing-after-results-are-known, I pre-committed the following decision rule before running either: *the post-hoc TF-IDF baseline is reported as the headline contribution of this study only if it (i) matches or exceeds the autoencoder on the aggregate hit-rate at any k, and (ii) reproduces the autoencoder's per-cohort rank ordering on the cohort with the smallest pre-registered MW p-value. The post-hoc entity-masking ablation is reported as defensive evidence on Lehman only if the rank delta is at most one position.* Both conditions held: TF-IDF aggregate hit@5 = 0.40 vs autoencoder 0.20 with the same Lehman-as-top-cohort ordering, and Lehman's entity-masking rank delta is zero. Had either condition failed, both analyses would have been demoted to the appendix. Documenting the rule explicitly is the only way the post-hoc analyses earn equal evidentiary weight with the pre-registered primary result.

## 7. Results

### 7.1 Methodological exclusion of Enron

Enron's FY2000 10-K was filed on 2001-04-02. The earliest filing in any other cohort is Tyco's, dated 2001-12-28 — 270 days later. Under the spec's strict leave-one-cohort-out plus time-controlled rule (training data = clean filings from *other* cohorts AND dated ≤ that fraud's filing date), Enron's eligible training set is empty. No autoencoder was trained for Enron; no per-filing score, no rank, no Mann-Whitney result, no bootstrap CI, no null-permutation p-value can be reported for Enron without violating the frozen spec.

This is the correct outcome of the contract, not a workaround for missing data. The honest reading is also the most uncomfortable one: the pre-registered design was infeasible for the most famous fraud in the dataset, and the design freeze did not catch this. That is a finding about pre-registration, not about fraud detection. It also illustrates a real generalizable problem in held-out evaluation under temporal constraints: when the held-out positive examples include the chronologically earliest one in the eligible universe, time-controlled training has no out-of-sample data to consume. Future work that attempts the same design should either expand the training universe to clean filings outside the held-out cohorts (which the LOCO rule would still permit, time-controlled), or accept exclusion as a possible outcome and frame the held-out set with that in mind.

### 7.2 Per-fraud rank under the pre-registered autoencoder (5 of 6 cohorts)

**Table 2. Pre-registered autoencoder results, single-pass against frozen spec.** Rank 1 = highest mean per-sentence reconstruction error within the cohort. Random-baseline expected rank for cohort size N is (N+1)/2 ≈ 6–7. MW p is one-sided "fraud > peers"; effect size is rank-biserial correlation in [-1, 1].

| Fraud | Cohort N | Rank | Percentile | Bootstrap 95% CI | MW *p* | MW effect | Null-permutation *p* | Train-set sentences |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Lehman (LEH) | 13 | **3** | 83.3 | [1, 6] | 1.3 × 10⁻⁹ | +0.12 | 0.244 | 3,367 |
| HealthSouth (HRC) | 12 | 7 | 45.5 | [4, 10] | 1.0 | −0.17 | 0.583 | 2,283 |
| Valeant (VRX) | 13 | 8 | 41.7 | [5, 11] | 1.0 | −0.19 | 0.602 | 4,327 |
| Tyco (TYC) | 13 | 9 | 33.3 | [6, 12] | 1.0 | −0.14 | 0.683 | 861 |
| WorldCom (WCOM) | 13 | 12 | 8.3 | [10, 13] | 1.0 | −0.15 | 0.937 | 1,477 |

Lehman is the only cohort that ranks among the top three. The Mann-Whitney p-value of 1.3 × 10⁻⁹ on Lehman is small but must be read alongside two other numbers: the rank-biserial effect size of +0.12 (small), and the per-sentence sample sizes of 1,051 fraud sentences against 5,763 peer sentences (large). Sentence-level p-values scale aggressively with sentence count under fixed effect size; this is the primary reason the rank-biserial effect is the more honest summary statistic. The other four cohorts produced negative effect sizes — fraud per-sentence errors were *lower* than peers' — meaning the autoencoder's signal on those cohorts is in the opposite of the predicted direction, and the corresponding MW p-values trivially exceed 0.5 because the test is one-sided.

### 7.3 Aggregate hit@k vs random baseline

Across the five LOCO cohorts:

| Metric | Observed | Random baseline |
|---|---:|---:|
| hit@1 | 0.00 | 0.08 |
| hit@3 | 0.20 | 0.23 |
| hit@5 | 0.20 | 0.39 |

The observed hit-rates fall at or *below* random expectation across all three thresholds. Hit@3 = 0.20 corresponds entirely to Lehman; hit@5 = 0.20 corresponds entirely to Lehman as well, since no other cohort's fraud reached rank 5.

### 7.4 Trivial baseline matches or exceeds the autoencoder on every cohort

**Table 3. Post-hoc TF-IDF + SVD32 baseline, same training corpora and same five cohorts.**

| Fraud | AE rank | TF-IDF rank | AE MW *p* | TF-IDF MW *p* | AE effect | TF-IDF effect |
|---|---:|---:|---:|---:|---:|---:|
| Lehman (LEH) | 3 | **1** | 1.3 × 10⁻⁹ | **5.0 × 10⁻²²** | +0.12 | **+0.19** |
| HealthSouth (HRC) | 7 | 6 | 1.0 | 0.997 | −0.17 | −0.10 |
| Valeant (VRX) | 8 | 8 | 1.0 | 1.0 | −0.19 | −0.15 |
| Tyco (TYC) | 9 | 6 | 1.0 | 0.64 | −0.14 | −0.01 |
| WorldCom (WCOM) | 12 | 12 | 1.0 | 1.0 | −0.15 | −0.14 |

The TF-IDF + SVD32 baseline matches the autoencoder on Valeant and WorldCom and outperforms it on Lehman, HealthSouth, and Tyco — three of five cohorts. On Lehman, the trivial baseline lands the fraud at rank 1 of 13 with a Mann-Whitney p-value of 5 × 10⁻²² and a rank-biserial effect size of +0.19, both stronger than the autoencoder. Aggregate hit-rates for the trivial baseline are hit@1 = 0.20, hit@3 = 0.20, hit@5 = 0.40, with the random baseline at 0.08, 0.23, 0.39 — the trivial baseline is the only configuration in this study that produces an aggregate hit rate above the random baseline at any k.

The interpretation requires care. The trivial baseline being competitive does not validate the autoencoder; it indicates that whatever signal exists at this dataset size is captured by sentence-level vocabulary distinctiveness alone, not by anything the neural autoencoder additionally represents. The signal that survives is text-distributional, not deep-learning-specific. At N = 6, on this single signal, the 2020s neural model contributes nothing beyond a 1990s latent-semantic-analysis baseline.

### 7.5 Lehman's positive result is robust to entity masking

The post-hoc entity-masking ablation tests one specific contamination concern: did MiniLM's web-pretraining seed Lehman's positive rank by memorizing literal mentions of "Lehman", "Fuld", "Repo 105", or auditor names? After masking 93 such mentions in Lehman's MD&A (and replacing each with the literal token `[ENTITY]`), re-encoding, and rescoring against Lehman's existing autoencoder:

| Cohort | Replacements | Original rank | Masked rank | Δ |
|---|---:|---:|---:|---:|
| LEH | 93 | **3 / 13** | **3 / 13** | 0 |
| HRC | 6 | 7 / 12 | 7 / 12 | 0 |
| TYC | 93 | 9 / 13 | 11 / 13 | +2 |
| VRX | 31 | 8 / 13 | 9 / 13 | +1 |
| WCOM | 267 | 12 / 13 | 12 / 13 | 0 |

The matching 93-replacement counts for LEH and TYC are coincidental rather than a copy-paste artifact: Lehman decomposes as 64 mentions of "Lehman" + 29 mentions of "Lehman Brothers", while Tyco decomposes as 87 mentions of "Tyco" + 6 mentions of "ADT". The two cohorts use entirely disjoint entity-token lists in `scripts/10_entity_masking_posthoc.py` and the matching total is a contingent fact about these particular two filings.

Lehman's rank is invariant under entity masking. The literal-name-leakage hypothesis fails to explain Lehman's positive result. This does not address topical leakage — MiniLM may still have seen general post-2008 commentary about repo accounting, off-balance-sheet vehicles, or investment-bank insolvency that influenced its representations. That residual contamination concern remains disclosed but unaddressed empirically.

### 7.6 Leave-one-fraud-out aggregate sensitivity

Removing each fraud in turn from the aggregate does not produce a regime under which the four-fraud aggregate beats the random baseline. Detailed numbers are in `data/results/aggregate_metrics.json`. Removing Lehman drops hit@3 and hit@5 to 0.00 across the remaining four cohorts; removing any other cohort leaves Lehman as the sole positive contributor. The aggregate result is entirely dependent on Lehman.

### 7.7 Honest interpretation

The numbers admit two readings, both of which are consistent with the data:

1. *The single signal has no real out-of-sample power at N = 6.* What looks like a positive on Lehman is one observation drawn from the cohort with the largest training set (3,367 training sentences vs. Tyco's 861, a factor-of-four asymmetry), and bootstrap CIs are wide on every cohort. The TF-IDF baseline matching the autoencoder is consistent with this reading.
2. *MD&A language is too heterogeneous for a single autoencoder reconstruction-error signal to discriminate fraud from clean peers without supervision.* Sector- and year-matched peer cohorts are coarse — within a SIC-2-digit code, business models and disclosure styles vary widely.

Both readings produce the same conclusion: at this dataset size, on this signal, the answer to the driving question is no. I report the result as it stands; I did not iterate the autoencoder, peer construction, or scoring after observing these numbers, per the frozen-spec contract.

## 8. Conclusions, Limitations, Future Work

Three substantive findings emerged from this project.

**The first finding is the headline.** A pre-registered single-signal unsupervised novelty study on SEC 10-K MD&A text, evaluated under strict leave-one-cohort-out plus time-controlled training against six historical fraud filings, produces a negative result. Of five evaluable cohorts, four rank fraud filings at or below the random-baseline expectation. The single positive cohort (Lehman, rank 3 of 13) is matched or exceeded by a 1990s-era TF-IDF + truncated-SVD trivial baseline, which lands Lehman at rank 1 of 13 with a stronger Mann-Whitney signal. At N = 6, on this specific signal, the autoencoder adds nothing beyond a baseline a careful undergraduate could have implemented in 1995.

**The second finding is structural.** The pre-registered design was infeasible for Enron. Under leave-one-cohort-out plus time-controlled training, the chronologically earliest held-out positive example has no eligible training data; Enron's accession was committed to the spec, and the design freeze did not catch the consequence. That is a finding about pre-registration discipline, not about fraud-detection capability. It is also a generalizable lesson: any held-out evaluation under temporal constraints must verify that every held-out positive admits at least one eligible training cohort under the proposed rule, before the spec is frozen. Future work in this paradigm should adopt that pre-flight check.

**The third finding is the trivial-baseline gap.** The most decisive result in this study is not the autoencoder's per-fraud ranks but the post-hoc TF-IDF + SVD32 baseline matching or exceeding the autoencoder on every cohort. Without that baseline, the project would have reported "Lehman is detectable" as the clean positive. With it, the honest claim is "Lehman is detectable by both methods, and the more expensive method does not beat the cheaper one." If a CSC 44800 takeaway is the deliverable, this is it: a sharp baseline is not optional, and a result that does not survive a baseline check is not a result.

Three lessons follow.

*Pre-registration is load-bearing only if it survives contact with the data.* The frozen spec held: I did not iterate the autoencoder, did not redefine "clean," did not modify peer matching, and did not retreat from the Enron exclusion when the result was uncomfortable. The post-hoc analyses (TF-IDF baseline, entity-masking ablation) are clearly labeled as such and do not displace the primary numbers in `data/results/per_fraud_metrics.json`. The frozen-spec contract is what makes the negative result informative; without it, the same numbers would be a polite request to redesign and rerun.

*Methodological exclusions are content, but only if owned.* Section 7.1 reports Enron's exclusion as a finding because the alternative would have been to relax the spec post-hoc and rerun. The exclusion is a design error, named as such; the transparency of naming it is what converts a missing data point into a teaching example. Any future design that proposes leave-one-cohort-out plus time-controlled training over a temporally-ordered positive set should require, as a pre-flight check, that every held-out positive be scoreable under the proposed rule before the spec is frozen.

*The Lehman confound is real, partially refuted by my own data, and named.* Lehman's autoencoder was trained on 3,367 sentences from 43 filings — a large training corpus, nearly four times Tyco's 861 sentences from 11 filings. The intuition that "Lehman wins because Lehman has more training data" is the obvious reading, and an early draft of this section argued exactly that. The data refute it. Valeant's autoencoder was trained on **4,327 sentences from 55 filings** — *more* training data than Lehman — and Valeant ranks 8 of 13, statistically indistinguishable from random. If training-corpus size alone explained the Lehman result, Valeant should outrank Lehman; it does not. The confound therefore narrows to "Lehman-specific signal" or "Lehman-specific peer pool," not "training data quantity." The TF-IDF baseline produces the same Lehman-specific result with a stronger Mann-Whitney statistic, which weakly argues for a real text-distributional Lehman signature rather than for a method-specific artifact. I report the Lehman result as n = 1 with the confound named and partially refuted, and decline to claim a method.

**Limitations.** N = 6 (effective N = 5) is too small for confidence intervals to constrain anything tightly; the bootstrap CIs in Section 7.2 are wide. MiniLM pretraining contamination beyond literal-name leakage was not addressed empirically. SIC-2-digit + same-fiscal-year peer matching is coarse and admits residual heterogeneity in size, geography, and business model. EDGAR's currently-reported SIC differs in some cases from the firm's at-time-of-filing SIC; symmetric application is the cleanest available rule but does not fully control for sector-at-filing. The operational "clean" rule is editable-deny-list-only — partial coverage, transparent about what could not be verified. The autoencoder bottleneck dimension was frozen at 32 without a sensitivity sweep; bottleneck-dimension sensitivity is an obvious gap.

**Future work.** The most informative single direction the data point to is *change-detection within firm*: instead of comparing a fraud filing's MD&A against industry peers in the same year, compare it against the same firm's prior-year MD&A. This controls for firm-specific style at the cost of losing the fraud-vs-clean comparison, and it converts the question from "is this filing anomalous against peers" to "is this filing anomalous against itself." A second direction is multi-section integration, particularly Item 1A risk factors, which are absent from this study because the pre-registered scope was Item 7 only. A third is structured + unstructured fusion: combining MD&A-derived signals with financial-statement ratios and audit-committee disclosures in a single model. A fourth is a genuinely larger held-out set: the SEC's AAER list is in the low thousands across all years, and a serious version of this study would condition on AAER-confirmed fraud rather than the high-profile six examined here. The single most cost-effective next step before any of the above is a within-firm baseline on the existing six cohorts — same parser, same MiniLM embeddings, same TF-IDF baseline, but the comparison set is the firm's own prior 10-K rather than peers. That is the falsifiable Lehman-specificity check this study could not run.

## References

Russell, S., & Norvig, P. (2020). *Artificial Intelligence: A Modern Approach* (4th ed.). Pearson. (CSC 44800 textbook; cited for general framing of supervised vs. unsupervised learning, empirical evaluation methodology, and held-out evaluation.)

Burden, R. L., & Faires, J. D. (2010). *Numerical Analysis* (9th ed.). Brooks/Cole. (Cited for the bootstrap and null-permutation methodology.)

Cecchini, M., Aytug, H., Koehler, G. J., & Pathak, P. (2010). Making words work: Using financial text as a predictor of financial events. *Decision Support Systems*, 50(1), 164–175.

Loughran, T., & McDonald, B. (2011). When is a liability not a liability? Textual analysis, dictionaries, and 10-Ks. *The Journal of Finance*, 66(1), 35–65.

Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. In *Proceedings of EMNLP-IJCNLP 2019*.

U.S. Securities and Exchange Commission. *EDGAR full-text search and submissions JSON.* Public access at https://www.sec.gov/edgar.

U.S. Securities and Exchange Commission. *Accounting and Auditing Enforcement Releases (AAERs).* Public access at https://www.sec.gov/divisions/enforce/friactions.shtml.

Project repository: https://github.com/ArseniiChan/canary. All code, frozen spec, deny-lists, parsed MD&A index, training logs, single-pass validation outputs, post-hoc baseline outputs, and figures are committed to the repo at the validation freeze tag and the post-hoc tag.

---

## Appendix A — Frozen analysis spec

See `analysis_spec.md`, git tag `validation-spec-frozen` (committed 2026-05-01).

## Appendix B — Cohort overview

See `reports/cohort_overview.md`. Per-cohort peer lists, clean-rule outcomes per peer, SIC distribution within each cohort.

## Appendix C — Parsing QA

See `reports/parsing_qa.md`. Extraction success rate by fraud-vs-peer status and by year; per-filing parse method and character/sentence counts; failure list.

## Appendix D — Post-hoc analyses

* TF-IDF + SVD32 trivial baseline: `data/results/scores_tfidf.csv`, `data/results/per_fraud_metrics_tfidf.json`. Script: `scripts/09_tfidf_baseline.py`.
* Entity-masking ablation across the five LOCO cohorts: `data/results/entity_masking_posthoc.json`. Script: `scripts/10_entity_masking_posthoc.py`.

Both are clearly labeled post-hoc and exploratory and do not displace the primary results in `data/results/per_fraud_metrics.json`.

## Appendix E — Reproducibility

```bash
make install          # one-time
make pin-accessions   # Phase 0; commits and tags analysis_spec.md
make reproduce        # full pipeline from data/raw cache through figures
make test             # 36 unit tests
.venv/bin/python scripts/09_tfidf_baseline.py            # post-hoc TF-IDF baseline
.venv/bin/python scripts/10_entity_masking_posthoc.py    # post-hoc entity-masking
.venv/bin/python scripts/11_baseline_comparison_figures.py
```

Every figure in `reports/figures/` is regenerated by `scripts/07_generate_figures.py` (primary) and `scripts/11_baseline_comparison_figures.py` (post-hoc) from `data/results/`. Random seeds for `numpy`, `torch`, and Python `random` are fixed at 42.
