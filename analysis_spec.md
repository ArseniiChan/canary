# Canary — Frozen Analysis Specification

**Status:** This file is the frozen analysis spec. It is committed to git 
and tagged `validation-spec-frozen` BEFORE Phase 5 validation runs. Single-pass 
results from `scripts/06_validate.py` are reported as-is.

**Generated:** 2026-05-01

## 1. Held-out fraud evaluation set (six 10-K filings, all pre-discovery)

| # | Company | CIK | FY | Accession | Filed | Period | Pre-discovery | SIC | SIC desc |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Enron Corp. | 0001024401 | 2000 | `0001024401-01-500010` | 2001-04-02 | 2000-12-31 | OK | 6200 | Security & Commodity Brokers, Dealers, Exchanges & Services |
| 2 | WorldCom Inc. | 0000723527 | 2001 | `0001005477-02-001226` | 2002-03-13 | 2001-12-31 | OK | 4813 | Telephone Communications (No Radiotelephone) |
| 3 | Tyco International Ltd. | 0000833444 | 2001 | `0000912057-01-544874` | 2001-12-28 | 2001-09-30 | OK | 3585 | Air-Cond & Warm Air Heatg Equip & Comm & Indl Refrig Equip |
| 4 | HealthSouth Corp. | 0000785161 | 2001 | `0001005150-02-000448` | 2002-03-27 | 2001-12-31 | OK | 8060 | Services-Hospitals |
| 5 | Valeant Pharmaceuticals International Inc. | 0000885590 | 2014 | `0000885590-15-000015` | 2015-02-25 | 2014-12-31 | OK | 2834 | Pharmaceutical Preparations |
| 6 | Lehman Brothers Holdings Inc. | 0000806085 | 2007 | `0001104659-08-005476` | 2008-01-29 | 2007-11-30 | OK | 6211 | Security Brokers, Dealers & Flotation Companies |

### Per-target verification detail

#### Enron Corp. (`ENE`)

- EDGAR entity name: `ENRON CORP/OR/`
- CIK: `0001024401`  ·  SIC: `6200` (Security & Commodity Brokers, Dealers, Exchanges & Services)
- Fiscal year: **2000**
- Accession (frozen): `0001024401-01-500010`
- Filing date: **2001-04-02**
- Period of report: 2000-12-31
- Primary document: `ene10-k.txt`
- Primary doc URL: <https://www.sec.gov/Archives/edgar/data/1024401/000102440101500010/ene10-k.txt>
- Primary doc size: 320,297 bytes
- Primary doc SHA-256: `940e08b26b70e518782447a3b344012f84d374acef23d9f9646f2fe5522326d4`
- Public revelation date: **2001-10-16**
- Revelation event: Q3 earnings release: $618M loss, $1.2B equity write-down
- Source for revelation date: SEC complaint; press archive (Wall Street Journal, Houston Chronicle, Oct 17 2001)
- **Verified pre-discovery:** 197 days between filing and revelation.

#### WorldCom Inc. (`WCOM`)

- EDGAR entity name: `MCI INC`
- CIK: `0000723527`  ·  SIC: `4813` (Telephone Communications (No Radiotelephone))
- Fiscal year: **2001**
- Accession (frozen): `0001005477-02-001226`
- Filing date: **2002-03-13**
- Period of report: 2001-12-31
- Primary document: `d02-36461.txt`
- Primary doc URL: <https://www.sec.gov/Archives/edgar/data/723527/000100547702001226/d02-36461.txt>
- Primary doc size: 739,765 bytes
- Primary doc SHA-256: `fe5bd8e19daa6c6b4c70ea3b61077392bc764e9ed523ae35152a711a1221e6e9`
- Public revelation date: **2002-06-25**
- Revelation event: Announcement of $3.8B accounting fraud (line-cost capitalization)
- Source for revelation date: SEC AAER 1568 / SEC press release Jun 26 2002
- **Verified pre-discovery:** 104 days between filing and revelation.

#### Tyco International Ltd. (`TYC`)

- EDGAR entity name: `Johnson Controls International plc`
- CIK: `0000833444`  ·  SIC: `3585` (Air-Cond & Warm Air Heatg Equip & Comm & Indl Refrig Equip)
- Fiscal year: **2001**
- Accession (frozen): `0000912057-01-544874`
- Filing date: **2001-12-28**
- Period of report: 2001-09-30
- Primary document: `a2062534z10-k.txt`
- Primary doc URL: <https://www.sec.gov/Archives/edgar/data/833444/000091205701544874/a2062534z10-k.txt>
- Primary doc size: 495,538 bytes
- Primary doc SHA-256: `30080bab125eeced95ce44626cba79e9a4949272d72075c9933ea935738c877b`
- Public revelation date: **2002-06-03**
- Revelation event: Indictment of CEO L. Dennis Kozlowski (NY DA)
- Source for revelation date: NY District Attorney filings; SEC litigation release LR-17722
- **Verified pre-discovery:** 157 days between filing and revelation.

#### HealthSouth Corp. (`HRC`)

- EDGAR entity name: `Encompass Health Corp`
- CIK: `0000785161`  ·  SIC: `8060` (Services-Hospitals)
- Fiscal year: **2001**
- Accession (frozen): `0001005150-02-000448`
- Filing date: **2002-03-27**
- Period of report: 2001-12-31
- Primary document: `form10k.txt`
- Primary doc URL: <https://www.sec.gov/Archives/edgar/data/785161/000100515002000448/form10k.txt>
- Primary doc size: 401,045 bytes
- Primary doc SHA-256: `c3c8a1965b187f98675332605ddb6427b6874ff43d6e795513f8a8228bf09203`
- Public revelation date: **2003-03-19**
- Revelation event: SEC civil complaint alleging $2.7B fraud
- Source for revelation date: SEC litigation release LR-18044
- **Verified pre-discovery:** 357 days between filing and revelation.

#### Valeant Pharmaceuticals International Inc. (`VRX`)

- EDGAR entity name: `Bausch Health Companies Inc.`
- CIK: `0000885590`  ·  SIC: `2834` (Pharmaceutical Preparations)
- Fiscal year: **2014**
- Accession (frozen): `0000885590-15-000015`
- Filing date: **2015-02-25**
- Period of report: 2014-12-31
- Primary document: `valeant2014form10-k.htm`
- Primary doc URL: <https://www.sec.gov/Archives/edgar/data/885590/000088559015000015/valeant2014form10-k.htm>
- Primary doc size: 4,549,035 bytes
- Primary doc SHA-256: `c02ddd8fa83f6928ac815aaf97dcb071ade77a69be72f488321dbfa22b9386e7`
- Public revelation date: **2015-10-19**
- Revelation event: Citron Research short report alleging Philidor channel stuffing
- Source for revelation date: Citron Research published report Oct 21 2015 (initial allegations Oct 19 in social media); subsequent SEC investigation
- **Verified pre-discovery:** 236 days between filing and revelation.

#### Lehman Brothers Holdings Inc. (`LEH`)

- EDGAR entity name: `LEHMAN BROTHERS HOLDINGS INC. PLAN TRUST`
- CIK: `0000806085`  ·  SIC: `6211` (Security Brokers, Dealers & Flotation Companies)
- Fiscal year: **2007**
- Accession (frozen): `0001104659-08-005476`
- Filing date: **2008-01-29**
- Period of report: 2007-11-30
- Primary document: `a08-3530_110k.htm`
- Primary doc URL: <https://www.sec.gov/Archives/edgar/data/806085/000110465908005476/a08-3530_110k.htm>
- Primary doc size: 6,314,293 bytes
- Primary doc SHA-256: `0e200f493b7c478b4a3d5d165e9541be72d808de62e4a3d8b3fe651f8d700da4`
- Public revelation date: **2008-09-15**
- Revelation event: Chapter 11 bankruptcy filing (Repo 105 disclosed in Mar 2010 examiner's report)
- Source for revelation date: Bankruptcy court docket; Valukas examiner's report (Mar 2010)
- **Verified pre-discovery:** 230 days between filing and revelation.

## 2. Frozen primary configuration

```
embedding model       : sentence-transformers/all-MiniLM-L6-v2  (dim=384)
autoencoder           : 384 -> 128 -> 32 -> 128 -> 384, ReLU, MSE, Adam(lr=1e-3)
training              : 200 epochs, batch 16, 20% validation split, early stopping
seeds                 : numpy=42, torch=42, python=42
sentence cap          : 100 per filing during training (uniform sample if more)
filing-level score    : mean per-sentence reconstruction error
statistical test      : Mann-Whitney U on fraud vs peer sentence-level errors
bootstrap             : 1,000 filing-level resamples within cohort
null permutation      : 1,000 within-cohort label shuffles
training regime       : leave-one-cohort-out + time-controlled (filings <= fraud filing date)
peer matching         : SIC-2-digit + same fiscal year; SIC-1 fallback if SIC-2 < 6
clean-peer rule       : no AAER + no Item 4.02 / 10-K/A within 5 yrs + no class-action settlement > $1M within 5 yrs
primary aggregation   : mean (ablations: trimmed-mean@5%, max — appendix only)
primary sentence cap  : 100 (ablations: 50, 200 — appendix only)
entity-masking ablation: Enron only, appendix
```

## 3. Reporting metrics (per fraud + aggregate)

- Cohort size, exact rank within cohort, percentile rank
- Hit@1, Hit@3, Hit@5 paired with random-baseline expected value
- Mann-Whitney U statistic, p-value, effect size (rank-biserial)
- Bootstrap 95% CI on rank (1,000 filing-level resamples)
- Null-permutation empirical p-value of `rank <= k` (1,000 permutations)
- Leave-one-fraud-out aggregate sensitivity (Section 6 of report)

## 4. Phase 1 cohorts (filled in by `scripts/01_pull_filings.py`)

Per-fraud SIC-2 cohort lists (CIK + accession + filing date) appended after Phase 1, documenting any SIC-1 fallbacks separately. Fallback cohorts are excluded from primary results and reported separately.

---

**Once this file is committed and tagged `validation-spec-frozen`, 
no further edits to the analysis configuration are made before validation. 
Whatever the numbers say, that's the result.**
