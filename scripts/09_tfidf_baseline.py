"""Phase 6 (post-hoc): TF-IDF + truncated-SVD trivial baseline.

For each of the 5 cohorts that have a LOCO + time-controlled autoencoder, build
the same training corpus the autoencoder saw (clean peer sentences from OTHER
cohorts dated <= that fraud's filing date), fit a TF-IDF -> TruncatedSVD(k=32)
pipeline, and use ``||x - U U^T x||^2`` per sentence as the reconstruction-error
analog. Bottleneck k=32 matches the autoencoder.

This baseline is descriptive and exploratory: it answers the question
"does a textbook 1990s-era latent-semantic-analysis novelty detector match the
autoencoder?" If yes, the autoencoder is decoration on this dataset. If no,
the autoencoder is justified.

Outputs:
  data/results/scores_tfidf.csv     # one row per filing, mirrors scores.csv schema
  data/results/per_fraud_metrics_tfidf.json
  data/results/per_fraud_summary_tfidf.csv
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.parsing import split_sentences
from engine.stats import (
    bootstrap_rank_ci,
    mann_whitney_fraud_vs_peers,
    null_permutation_p,
    rank_fraud_in_cohort,
)

SEED = 42
SVD_K = 32
SENTENCE_CAP = 100  # match autoencoder training cap


def parsed_text(accession: str) -> str:
    p = REPO_ROOT / f"data/processed/parsed/{accession.replace('-', '')}.txt"
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def filing_sentences(accession: str) -> list[str]:
    body = parsed_text(accession)
    if not body:
        return []
    return split_sentences(body)


def cohort_training_corpus(
    cohort_id: str,
    cohorts: list[dict],
    rng: np.random.Generator,
) -> list[str]:
    """Replay the autoencoder LOCO + time-controlled rule to assemble the
    sentence corpus the autoencoder saw."""
    target = next(c for c in cohorts if c["fraud_ticker"] == cohort_id)
    target_date = target["fraud_filing_date"]

    sents: list[str] = []
    for c in cohorts:
        if c["fraud_ticker"] == cohort_id:
            continue
        for p in c["peers"]:
            if not p.get("is_clean"):
                continue
            if p["filing_date"] > target_date:
                continue
            ss = filing_sentences(p["accession"])
            if not ss:
                continue
            if len(ss) > SENTENCE_CAP:
                idx = rng.choice(len(ss), size=SENTENCE_CAP, replace=False)
                ss = [ss[i] for i in sorted(idx)]
            sents.extend(ss)
    return sents


def fit_pipeline(corpus: list[str]) -> tuple[TfidfVectorizer, TruncatedSVD]:
    vec = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        max_features=20000,
        ngram_range=(1, 1),
        sublinear_tf=True,
    )
    X = vec.fit_transform(corpus)
    n_features = X.shape[1]
    k = min(SVD_K, n_features - 1, X.shape[0] - 1)
    svd = TruncatedSVD(n_components=k, random_state=SEED)
    svd.fit(X)
    return vec, svd


def per_sentence_recon_error(
    vec: TfidfVectorizer, svd: TruncatedSVD, sentences: list[str]
) -> np.ndarray:
    if not sentences:
        return np.zeros((0,), dtype=np.float32)
    X = vec.transform(sentences)
    Z = svd.transform(X)
    Xhat = svd.inverse_transform(Z)
    diff = X.toarray() - Xhat
    err = (diff ** 2).mean(axis=1)
    return err.astype(np.float32)


def score_filing(vec, svd, sentences) -> tuple[float, np.ndarray]:
    err = per_sentence_recon_error(vec, svd, sentences)
    if err.size == 0:
        return float("nan"), err
    return float(err.mean()), err


def main() -> int:
    cohorts = json.loads((REPO_ROOT / "data/processed/cohorts.json").read_text())["cohorts"]
    fraud_manifest = json.loads((REPO_ROOT / "data/processed/fraud_manifest.json").read_text())
    fraud_by_ticker = {f["ticker"]: f for f in fraud_manifest["frauds"] if f["status"] == "OK"}

    out_dir = REPO_ROOT / "data/results"
    out_dir.mkdir(parents=True, exist_ok=True)

    score_rows: list[dict] = []
    per_sentence_cache: dict[str, np.ndarray] = {}  # cohort__accession -> per-sentence err

    rng = np.random.default_rng(SEED)
    cohort_ids = ["HRC", "LEH", "TYC", "VRX", "WCOM"]

    for cid in cohort_ids:
        cohort = next(c for c in cohorts if c["fraud_ticker"] == cid)
        print(f"[{cid}] assembling training corpus...")
        corpus = cohort_training_corpus(cid, cohorts, rng)
        if len(corpus) < 100:
            print(f"[{cid}] training corpus too small ({len(corpus)} sents) — skipping")
            continue
        print(f"[{cid}] fit on {len(corpus)} training sentences")
        vec, svd = fit_pipeline(corpus)

        # Score fraud
        fraud = fraud_by_ticker[cid]
        fraud_sents = filing_sentences(fraud["accession"])
        fraud_score, fraud_err = score_filing(vec, svd, fraud_sents)
        per_sentence_cache[f"{cid}__{fraud['accession']}"] = fraud_err
        score_rows.append({
            "filing_id": f"{cid}_fraud",
            "accession": fraud["accession"],
            "fraud_or_peer": "fraud",
            "cohort_id": cid,
            "cik": fraud["cik"],
            "filing_date": fraud["filing_date"],
            "report_date": fraud["report_date"],
            "n_sentences": len(fraud_sents),
            "score_mean": fraud_score,
        })

        # Score clean peers
        peer_count = 0
        for p in cohort["peers"]:
            if not p.get("is_clean"):
                continue
            ss = filing_sentences(p["accession"])
            if not ss:
                continue
            sc, err = score_filing(vec, svd, ss)
            per_sentence_cache[f"{cid}__{p['accession']}"] = err
            score_rows.append({
                "filing_id": f"{cid}_peer_{p['cik']}",
                "accession": p["accession"],
                "fraud_or_peer": "peer",
                "cohort_id": cid,
                "cik": p["cik"],
                "filing_date": p["filing_date"],
                "report_date": p["report_date"],
                "n_sentences": len(ss),
                "score_mean": sc,
            })
            peer_count += 1
        print(f"[{cid}] scored fraud + {peer_count} peers (TF-IDF)")

    # Write scores csv
    csv_path = out_dir / "scores_tfidf.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "filing_id", "accession", "fraud_or_peer", "cohort_id",
            "cik", "filing_date", "report_date",
            "n_sentences", "score_mean",
        ])
        w.writeheader()
        for r in score_rows:
            r2 = dict(r)
            r2["score_mean"] = f"{r['score_mean']:.6f}"
            w.writerow(r2)
    print(f"\nWrote {csv_path}")

    # Per-cohort metrics
    per_fraud: list[dict] = []
    for cid in cohort_ids:
        rows = [r for r in score_rows if r["cohort_id"] == cid]
        if not rows:
            continue
        fraud_row = next(r for r in rows if r["fraud_or_peer"] == "fraud")
        peer_rows = [r for r in rows if r["fraud_or_peer"] == "peer"]
        peer_scores = np.array([r["score_mean"] for r in peer_rows], dtype=float)

        rank = rank_fraud_in_cohort(cid, fraud_row["score_mean"], peer_scores)
        boot = bootstrap_rank_ci(cid, fraud_row["score_mean"], peer_scores, n_bootstrap=1000, seed=SEED)
        nullp = null_permutation_p(cid, fraud_row["score_mean"], peer_scores, n_permutations=1000, seed=SEED)

        fraud_err = per_sentence_cache[f"{cid}__{fraud_row['accession']}"]
        peer_err_concat = np.concatenate([
            per_sentence_cache[f"{cid}__{r['accession']}"] for r in peer_rows
        ])
        mw = mann_whitney_fraud_vs_peers(cid, fraud_err, peer_err_concat)

        per_fraud.append({
            "ticker": cid,
            "n_total": rank.n_total,
            "fraud_score": round(fraud_row["score_mean"], 6),
            "fraud_rank": rank.fraud_rank,
            "fraud_percentile": rank.fraud_percentile,
            "hit_at_1": rank.hit_at_1,
            "hit_at_3": rank.hit_at_3,
            "hit_at_5": rank.hit_at_5,
            "random_hit1": rank.random_hit1,
            "random_hit3": rank.random_hit3,
            "random_hit5": rank.random_hit5,
            "mw_u": mw.u_statistic,
            "mw_p": mw.p_value,
            "mw_effect_rank_biserial": mw.rank_biserial_effect,
            "mw_n_fraud_sent": mw.n_fraud_sentences,
            "mw_n_peer_sent": mw.n_peer_sentences,
            "boot_lower_95": boot.lower_95,
            "boot_upper_95": boot.upper_95,
            "null_p_le_observed": nullp.p_le_observed,
        })

    metrics_path = out_dir / "per_fraud_metrics_tfidf.json"
    metrics_path.write_text(json.dumps({"per_fraud": per_fraud, "method": "tfidf+svd32"}, indent=2) + "\n")
    print(f"Wrote {metrics_path}")

    summary_path = out_dir / "per_fraud_summary_tfidf.csv"
    with summary_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "n_total", "rank", "percentile",
                    "boot_lower_95", "boot_upper_95",
                    "mw_p", "mw_effect", "null_p_le_observed"])
        for r in per_fraud:
            w.writerow([
                r["ticker"], r["n_total"], r["fraud_rank"],
                f"{r['fraud_percentile']:.1f}",
                r["boot_lower_95"], r["boot_upper_95"],
                f"{r['mw_p']:.3g}", f"{r['mw_effect_rank_biserial']:.3f}",
                f"{r['null_p_le_observed']:.3f}",
            ])
    print(f"Wrote {summary_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
