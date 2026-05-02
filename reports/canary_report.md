# Canary — Single-Signal Unsupervised Novelty Study on SEC 10-K MD&A Text

**Course:** CSC 44800 — Artificial Intelligence (CCNY, Spring 2026)
**Author:** Arsenii Chan
**Advisor:** Prof. Erik K. Grimmelmann
**Repository:** https://github.com/ArseniiChan/canary
**Frozen analysis spec:** [analysis_spec.md](../analysis_spec.md) (git tag `validation-spec-frozen`)

---

## Abstract

**Can you flag accounting fraud a year early by reading the words in a
10-K?** This study pre-registers an answer for one specific signal: the
mean per-sentence reconstruction error of a PyTorch autoencoder
(384 → 128 → 32 → 128 → 384) trained on `all-MiniLM-L6-v2` sentence
embeddings of Management's Discussion and Analysis (Item 7) text. We
evaluate against six historical accounting frauds — Enron (FY2000),
WorldCom (FY2001), Tyco (FY2001), HealthSouth (FY2001), Valeant (FY2014),
Lehman Brothers (FY2007) — used strictly as a held-out evaluation set
whose pre-discovery filing dates are verified against documented
public-revelation events. Training is leave-one-cohort-out and
time-controlled: for each fraud cohort the model only sees clean peer
filings from <em>other</em> cohorts dated on or before that fraud's
filing date. The analysis spec is git-tagged `validation-spec-frozen`
before the validation script runs.

**Results.** Of the six cohorts, **Enron is excluded from primary results
by methodological necessity:** its filing date (2001-04-02) precedes every
peer filing in every other cohort, leaving zero training data under the
spec's strict LOCO + time-controlled rules. Of the remaining five cohorts,
**only Lehman Brothers ranks among the top three within its cohort
(rank 3/13, 83rd percentile)**; the other four (HRC 7/12, TYC 9/13, VRX
8/13, WCOM 12/13) rank at or below the random-baseline expectation.
Aggregate hit@1 = 0.00, hit@3 = 0.20, hit@5 = 0.20 — at or below random
(0.08, 0.23, 0.39). Mann-Whitney U on per-sentence reconstruction error
is significant only for Lehman (p ≈ 1.3e-09), but with a small
rank-biserial effect (+0.12); the other cohorts' MW tests favor peers,
not fraud. Bootstrap 95% CIs on rank are wide for every cohort.

We interpret this as a **negative result**: at N=6 frauds, with strict
out-of-sample evaluation, a single unsupervised novelty signal computed
over MD&A sentence embeddings does **not** reliably assign elevated
reconstruction error to historical fraud filings relative to
industry-and-year-matched clean peers. The discipline of the experiment
— frozen spec, LOCO + time-controlled training, no tuning to the
evaluation set — is what makes this finding informative.

This is a comparative novelty study, not a fraud detector. Limitations —
N=6 wide CIs, possible MiniLM pretraining contamination, peer-matching
residuals, parser-quality risk, and the Enron methodological constraint —
are discussed prominently and form the trust signal of this work.

## 1. Introduction

[TODO: Motivate the question. Public-company fraud has linguistic
fingerprints; a long literature in accounting and finance examines
disclosure language. We restrict the question to one signal, one test,
and a small held-out evaluation set, with the methodological discipline
of out-of-sample evaluation.]

## 2. Related Work

[TODO: Reference 4-6 papers spanning unsupervised anomaly detection,
sentence embeddings (BERT, MiniLM), prior MD&A NLP studies (Cecchini et
al.; Loughran-McDonald lexicon work), autoencoder anomaly detection
methodology, leave-one-out validation as standard practice.]

## 3. Methodology

### 3.1 Data

We download every primary 10-K document from SEC EDGAR for the six fraud
filings using the verified accession numbers in [analysis_spec.md](../analysis_spec.md).
Industry- and year-matched peer cohorts are constructed via SIC 2-digit
matching using EDGAR's currently-reported SIC code, with same calendar-year
period of report. Cohorts target 6-12 clean peers per fraud; SIC-1 fallback
is used only when SIC-2 yields fewer than 6 clean peers, and fallback
cohorts are reported separately and excluded from primary results.

#### Operational "clean" definition

A peer is clean iff:

1. The CIK is not on our editable AAER deny-list (sourced from public
   knowledge of SEC enforcement releases; partial coverage —
   see Limitations).
2. The same CIK has filed no 10-K/A within five years post-filing
   (programmatic via EDGAR submissions JSON).
3. The CIK or company name is not on our editable class-action deny-list
   (sourced from public knowledge of major settlements; partial coverage).

The deny-lists live at `data/processed/aaer_denylist.txt` and
`data/processed/classaction_denylist.txt`.

### 3.2 MD&A extraction

We extract the Item 7 (MD&A) section from each filing using a multi-strategy
parser ([engine/parsing.py](../engine/parsing.py)) that handles both the
SGML-era plain-text format (Enron, WorldCom, Tyco, HealthSouth) and the
modern HTML format (Valeant, Lehman). The parser:

* Strips HTML when present, normalizes whitespace.
* Locates the most likely (start, end) boundary pair from a prioritized
  candidate list: `(first Item 7 past TOC threshold, last Item 7A in
  document)` is the canonical pair; fallbacks include the
  "Management's Discussion and Analysis" body anchor for filings whose
  body MD&A header lacks the literal "Item 7" prefix (Tyco-style
  incorporation by reference).
* Filters out (Item 7, Item 7A) candidate pairs that appear within 1000
  characters of each other; such pairs are TOC entries, not real body
  headers.
* Rejects bodies that are unrealistically short (< 3,000 chars) or
  unrealistically long (> 400,000 chars).

We define a **hard gate** of >= 80% successful extraction across all
filings; the QA pipeline ([reports/parsing_qa.md](parsing_qa.md))
reports success rate by fraud/peer status and by year.

### 3.3 Single signal — autoencoder reconstruction error

Each filing's MD&A is sentence-tokenized using a regex-based splitter
that protects common abbreviations. Sentences shorter than 20 chars or
mostly digits are dropped. We embed each sentence using
`sentence-transformers/all-MiniLM-L6-v2` (384-dim) and cache the
result on disk per (filing, model, sentence-list).

For each fraud cohort C, we train one autoencoder under
**leave-one-cohort-out + time-controlled** conditions:

* **Training set** = clean peer filings from cohorts OTHER than C, AND
  whose `filing_date <= C's fraud filing_date`.
* **Architecture** = 384 → 128 → 32 → 128 → 384, ReLU activations,
  MSE loss, Adam (lr=1e-3), batch 16, 200 epochs with early stopping
  on a 20% validation split (patience 20).
* **Per-filing sentence cap of 100** during training (uniform sample
  if more) — prevents long-MD&A pseudoreplication.
* **Seeds** = 42 for numpy, torch, and Python's `random`.

At inference, the filing-level **score** = mean per-sentence reconstruction
error. Trimmed-mean@5% and max are computed and reported as descriptive
ablations only — they never enter the primary result.

### 3.4 Statistical defense

For each cohort:

* **Per-fraud rank** within the cohort (1 = highest reconstruction
  error), paired with random-baseline expectation (1/N for hit@1,
  and so on).
* **Mann-Whitney U** (one-sided "fraud > peers") on per-sentence
  reconstruction-error distributions; rank-biserial correlation
  reported as effect size.
* **Bootstrap 95% CI on rank** with 1,000 filing-level resamples
  with replacement.
* **Within-cohort null permutation** of P(rank <= observed) using 1,000
  random label assignments.
* **Leave-one-fraud-out** aggregate sensitivity.

## 4. Results

### 4.1 Methodological exclusion of Enron

Enron's FY2000 10-K was filed on 2001-04-02 — earlier than any peer
filing in any of the other five cohorts (the earliest is Tyco's
2001-12-28). Under the spec's strict LOCO + time-controlled rule
("training data = clean filings from OTHER cohorts AND dated ≤ that
fraud's filing date"), Enron's training set is empty. Rather than
relax the spec post-hoc (which the frozen-spec contract explicitly
forbids), we exclude Enron from primary results and document the
constraint as a finding: **time-controlled LOCO training is
unworkable for the chronologically earliest fraud in a held-out
evaluation set.** This is a structural limitation of the methodology
at this sample size, not a bug in the implementation.

### 4.2 Per-fraud rank (5 of 6 cohorts)

| Fraud | Cohort N | Rank | Percentile | Bootstrap 95% CI | MW p | MW effect | Null-permutation p |
|---|---:|---:|---:|---:|---:|---:|---:|
| Lehman (LEH) | 13 | **3** | 83.3 | [1, 6] | 1.3e-09 | +0.12 | 0.244 |
| HealthSouth (HRC) | 12 | 7 | 45.5 | [4, 10] | 1.0 | −0.17 | 0.583 |
| Valeant (VRX) | 13 | 8 | 41.7 | [5, 11] | 1.0 | −0.19 | 0.602 |
| Tyco (TYC) | 13 | 9 | 33.3 | [6, 12] | 1.0 | −0.14 | 0.683 |
| WorldCom (WCOM) | 13 | 12 | 8.3 | [10, 13] | 1.0 | −0.15 | 0.937 |

Rank 1 = highest mean per-sentence reconstruction error within the
cohort (most "novel"). Random-baseline expected rank for a cohort of
size N is (N+1)/2 ≈ 6-7. MW p-values are one-sided "fraud > peers";
effect size is rank-biserial correlation in [−1, 1].

### 4.3 Aggregate hit@k vs random

| Metric | Observed | Random baseline |
|---|---:|---:|
| hit@1 | 0.00 | 0.08 |
| hit@3 | 0.20 | 0.23 |
| hit@5 | 0.20 | 0.39 |

The observed hit rates are at or **below** random expectation across
all three thresholds.

### 4.4 Leave-one-fraud-out sensitivity

Removing each fraud in turn does not produce a regime under which the
remaining four-fraud aggregate exceeds the random baseline. Detailed
LOFO numbers are in [data/results/aggregate_metrics.json](../data/results/aggregate_metrics.json).

### 4.5 Interpretation

Lehman is the only cohort showing a clear elevation; its
sentence-level Mann-Whitney p (1.3e-09) is small but the effect size
is modest (+0.12). The other four cohorts produce per-sentence
distributions in which the fraud's per-sentence reconstruction errors
are statistically *lower* than peers' (negative effect sizes), the
opposite of the predicted direction.

Two readings are consistent with this:

1. The single signal we tested has no real out-of-sample power at
   N=5; what looks like a positive in any one cohort can be ascribed
   to the wide bootstrap CIs at this sample size.
2. MD&A language is too heterogeneous, and SIC-2-digit + same-fiscal-year
   peer matching too coarse, for a single autoencoder reconstruction-error
   signal to discriminate fraud from clean peers without supervision.

We report the result as it stands; we did not iterate the autoencoder,
peer construction, or scoring after observing these numbers, per the
frozen-spec contract.

## 5. Limitations

This is the trust signal of the project — read carefully.

1. **N = 6 fraud examples (5 in primary results).** Confidence
   intervals on aggregate hit rates are wide. We report bootstrap
   CIs and leave-one-fraud-out sensitivity to make this explicit.
   Enron is excluded from primary results by the methodological
   constraint described in Section 4.1, not by analyst choice.
2. **MiniLM pretraining contamination.** `all-MiniLM-L6-v2` was
   pre-trained on the public web and may have seen post-2008
   commentary about these specific frauds. We pre-registered an
   entity-masking ablation on Enron as defensive evidence, but
   Enron has no native autoencoder under LOCO + time-controlled
   training (Section 4.1) and we declined to run the ablation
   against a non-native cohort model post-hoc. The contamination
   risk therefore remains disclosed but empirically unaddressed.
3. **Peer-matching residuals.** SIC 2-digit matching plus same fiscal
   year does not perfectly control for size, geography, or business
   model. EDGAR's currently-reported SIC may differ from a firm's
   2001-era SIC (e.g., Enron is currently classified as SIC 6200,
   Security & Commodity Brokers). We use what EDGAR currently reports
   for symmetric treatment.
4. **Parser-quality risk.** MD&A extraction hits the 80% threshold,
   but per-filing extraction quality varies. Manual extraction fixes,
   if any, are logged in `reports/parsing_qa.md` and are applied
   symmetrically to fraud and peer filings.
5. **Operational "clean" rule with partial coverage.** AAER and
   class-action screening were applied via editable deny-lists rather
   than systematic database lookups. We disclose this directly: a
   peer that committed undisclosed fraud could appear in the cohort.
   Empirically, this would push our null toward zero (peers behave
   more like frauds), making our test conservative — but readers
   should weigh this when interpreting results.
6. **Single signal, single test.** We do not compose multiple signals
   into a "Canary score." We report the single signal we tested and
   nothing else.

## 6. Future Work

[TODO: 5-6 directions: longitudinal within-firm change-detection;
multi-section integration (Item 1A risk factors, Item 8 financial
notes); structured + unstructured fusion; supervised baseline once
fraud-label set grows; re-running on more recent suspect cohorts;
cross-domain transfer to mutual-fund or municipal disclosures.]

## References

[TODO]

---

## Appendix A — Frozen analysis spec excerpts

See [analysis_spec.md](../analysis_spec.md), git tag `validation-spec-frozen`.

## Appendix B — Cohort overview

See [cohort_overview.md](cohort_overview.md). Per-cohort peer lists,
clean-rule outcomes, SIC-1 fallback flagging.

## Appendix C — Parsing QA

See [parsing_qa.md](parsing_qa.md). Extraction success rate by fraud/peer
status and by year, plus failure list for manual review.

## Appendix D — Ablations

* Sentence aggregation: mean (primary), trimmed-mean@5%, max
  ([data/results/scores.csv](../data/results/scores.csv) for raw values).
* Sentence cap: 100 (primary), 50, 200 — descriptive sensitivity.

The pre-registered entity-masking ablation on Enron was not run; see
Section 5 (Limitation 2) for the methodology rationale.

## Appendix E — Reproducibility

```bash
make install      # one-time
make pin-accessions
# > commit + git tag analysis_spec.md as `validation-spec-frozen` <
make reproduce    # full pipeline from data/raw cache through figures
make test         # unit tests
```

Every figure in `reports/figures/` is regenerated by
`scripts/07_generate_figures.py` from `data/results/`.
