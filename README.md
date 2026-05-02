# Canary

**A pre-registered single-signal novelty study on SEC 10-K MD&A text — CSC 44800 (CCNY, Spring 2026).**

Can a computer reading the words in a public company's annual report tell which companies turned out to be committing accounting fraud? This project tests one specific answer to that question, freezes the methodology before the validation runs, and reports the result as-is — including the part where a 1990s baseline matches the 2020s neural model.

The short version of what this repo is and what it found:

- **What it does.** Trains a small autoencoder (PyTorch, 384 → 128 → 32 → 128 → 384) on `all-MiniLM-L6-v2` sentence embeddings of the Management's Discussion & Analysis section (Item 7) of clean SEC 10-K filings, then scores six historical fraud filings (Enron, WorldCom, Tyco, HealthSouth, Valeant, Lehman Brothers) by their mean per-sentence reconstruction error against industry-and-year-matched peer cohorts.
- **What makes it different from a typical class project.** The full analysis specification (accession numbers, model architecture, training rule, statistical tests, sentence cap, seeds) was committed and git-tagged `validation-spec-frozen` *before* any validation script ran. The validation runs once. Whatever the numbers say, that is the result.
- **What it found.** A negative result, named honestly: of the six frauds, Enron is excluded by methodological necessity (the leave-one-cohort-out + time-controlled rule admits no eligible training data for the chronologically earliest fraud), and of the remaining five, only Lehman Brothers ranks in the top three within its cohort. A post-hoc TF-IDF + truncated-SVD trivial baseline matches or exceeds the autoencoder on every cohort, including a stronger Lehman result. At N = 6 frauds, on this single signal, the neural model adds nothing beyond a 1990s latent-semantic-analysis baseline.
- **What it is not.** Not a fraud detector. Not a working production system. Not a claim that any of the six frauds would have been "caught early." It is a comparative novelty study with N = 6, run honestly, reported as-is, and useful as evidence that pre-registration discipline can survive an uncomfortable result.

The full report is at [reports/canary_report.md](reports/canary_report.md); a one-page result summary follows.

## Headline numbers

**Pre-registered autoencoder, single-pass against frozen spec.** Rank 1 = highest mean per-sentence reconstruction error within the cohort. Random-baseline expected rank for cohort size *N* is (*N*+1)/2 ≈ 6–7.

| Fraud | Cohort N | Rank | Mann-Whitney *p* | Effect (rank-biserial) | Bootstrap 95% CI |
|---|---:|---:|---:|---:|---:|
| Lehman Brothers (LEH) | 13 | **3** | 1.3 × 10⁻⁹ | +0.12 | [1, 6] |
| HealthSouth (HRC) | 12 | 7 | 1.0 | −0.17 | [4, 10] |
| Valeant (VRX) | 13 | 8 | 1.0 | −0.19 | [5, 11] |
| Tyco (TYC) | 13 | 9 | 1.0 | −0.14 | [6, 12] |
| WorldCom (WCOM) | 13 | 12 | 1.0 | −0.15 | [10, 13] |
| **Enron (ENE)** | — | **excluded** | — | — | — |

Aggregate hit@1 = 0.00, hit@3 = 0.20, hit@5 = 0.20, against a random baseline of 0.08 / 0.23 / 0.39. Hit@3 and hit@5 are entirely Lehman.

**Post-hoc TF-IDF + truncated-SVD trivial baseline.** Same training corpora, same five cohorts. The trivial baseline matches the autoencoder on Valeant and WorldCom, beats it on Lehman, HealthSouth, and Tyco. On Lehman the trivial baseline is rank 1 of 13, *p* ≈ 5 × 10⁻²², effect +0.19 — a stronger detection than the neural autoencoder.

**Post-hoc entity-masking ablation.** Lehman's positive rank survives masking 93 mentions of "Lehman", "Fuld", "Repo 105", and the auditor of record (rank 3 → 3 unchanged). Literal-name-leakage from MiniLM pretraining is unlikely to be the driver of the Lehman signal; topical leakage remains disclosed but unaddressed.

The full results are at [data/results/](data/results/) — `per_fraud_metrics.json`, `per_fraud_summary.csv`, `aggregate_metrics.json`, `scores.csv` for the pre-registered run; `per_fraud_metrics_tfidf.json`, `scores_tfidf.csv`, `entity_masking_posthoc.json` for the post-hoc analyses.

## What you'll find in this repo

```
canary/
├── analysis_spec.md         # FROZEN + git-tagged before validation ran
├── engine/                  # Library: edgar client, parsing, embeddings,
│                            # autoencoder, scoring, statistics, SIC matching,
│                            # operational clean-screening
├── scripts/                 # Phases 0-7 + post-hoc 9-11
├── tests/                   # 36 unit tests, all passing
├── data/
│   ├── processed/           # Cohorts, parsed MD&A, training log, deny-lists
│   └── results/             # Single-pass validation outputs + post-hoc
├── reports/                 # canary_report.md, parsing_qa.md, cohort_overview.md, figures/
├── dashboard/               # Next.js dashboard reading from data/results/
└── serve/                   # Modal-deployed FastAPI inference endpoint for /scan
```

## Reproducing the result from scratch

```bash
make install          # one-time: Python 3.12 venv + dependencies
make pin-accessions   # Phase 0: verify and pin EDGAR accessions
                      # commit + git-tag analysis_spec.md as validation-spec-frozen
make reproduce        # Phases 1-6: data, parse, embed, train, score,
                      # validate against frozen spec, regenerate figures
make test             # 36 unit tests

# Post-hoc analyses (council-recommended, clearly labeled non-primary):
.venv/bin/python scripts/09_tfidf_baseline.py
.venv/bin/python scripts/10_entity_masking_posthoc.py
.venv/bin/python scripts/11_baseline_comparison_figures.py
```

Random seeds for `numpy`, `torch`, and Python's `random` are fixed at 42 throughout. Embeddings are cached on disk per (filing, model). EDGAR fetches use the SEC's published 10-req/sec throttle with exponential-backoff retry on transient connection errors.

## What is deliberately NOT done

The report's Section 2 lists this in full; the short version: no supervised classifier on fraud labels; no Benford's Law on free text (wrong domain — a draft included it; the second adversarial review pointed out that Benford applies to financial-statement line items, not narrative); no foreign-issuer 20-Fs (incompatible with the Item 7 methodology); no autoencoder trained on a peer that is then scored from that same model; no training on filings dated after a fraud's filing date; no scoring of post-discovery 10-Ks; no "Canary score" composite; no claim that any fraud would have been "flagged N months early"; and no modification of the primary configuration after observing primary results.

## Methodology in one paragraph

For each of six historical accounting frauds, build a same-SIC-2-digit and same-fiscal-year peer cohort from EDGAR, screen each candidate against an operational clean rule (no AAER, no 10-K/A within 5 years post-filing, no class-action settlement). Extract Item 7 (MD&A) from each filing with a multi-strategy regex parser, sentence-tokenize, embed every sentence with `all-MiniLM-L6-v2`. For each held-out cohort, train a fresh autoencoder on clean peer sentences from *other* cohorts dated on or before that fraud's filing date (leave-one-cohort-out + time-controlled). Score each filing by mean per-sentence reconstruction error. Rank the fraud within its cohort. Run Mann-Whitney U on per-sentence error distributions, 1,000 filing-level bootstrap iterations on rank, 1,000 within-cohort null-permutation iterations, and leave-one-fraud-out aggregate sensitivity. Repeat the entire pipeline with TF-IDF + truncated-SVD as a post-hoc trivial baseline. Repeat the autoencoder pipeline with cohort-specific entity tokens replaced by `[ENTITY]` as a post-hoc literal-name-leakage check. Report all numbers single-pass against the frozen spec.

## Limitations

Read the full discussion in Section 8 of the report. The four big ones, in order of how much they constrain interpretation:

1. **N = 6 (effective N = 5) is small.** Bootstrap CIs are wide on every cohort. Aggregate findings can flip on the inclusion or exclusion of any single cohort.
2. **The Lehman confound is real, partially refuted by the data, and named.** The intuitive reading — "Lehman wins because Lehman's autoencoder had the most training data" — is wrong. Valeant's autoencoder was trained on 4,327 sentences (more than Lehman's 3,367) and ranks 8/13. If training-corpus size alone explained Lehman's rank, Valeant should outrank Lehman; it does not. The remaining unobservable confound is whether Lehman is detectable because of Lehman-specific signal or Lehman-specific peer pool, which is not separable at N=6.
3. **MiniLM pretraining contamination beyond literal-name leakage was not addressed empirically.** The post-hoc entity-masking ablation rules out one specific mechanism (literal-name memorization) and does not address topical leakage (post-2008 commentary about Repo 105 / off-balance-sheet vehicles / investment-bank insolvency, etc.).
4. **The operational "clean" rule is editable-deny-list-only.** AAER and class-action screening were not run against systematic databases; partial coverage is disclosed transparently. A peer that committed undisclosed fraud could appear in a cohort.

## License

MIT. Use it, replicate it, beat the baseline.

## Acknowledgments

CSC 44800 — Artificial Intelligence, City College of New York, Spring 2026. Advisor: Prof. Erik K. Grimmelmann. Engineering quality bar set by the companion CSC 30100 project at https://github.com/ArseniiChan/startup-growth-simulator.

Two adversarial review rounds and a five-advisor council deliberation shaped the methodology before code was written; a sixth council pass after the pre-registered validation forced the post-hoc TF-IDF baseline and the post-hoc entity-masking ablation into this report. The frozen-spec discipline survived all of it. Whatever the numbers say, that is the result.
