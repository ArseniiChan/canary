"""Phase 5 — single-pass validation against the frozen analysis spec.

Reads:
  data/results/scores.csv               (filing-level mean reconstruction error)
  data/processed/per_sentence/*.npy     (per-sentence reconstruction errors)
  data/processed/cohorts.json           (cohort manifest)
  data/processed/fraud_manifest.json    (fraud manifest)

Computes:
  * Per-fraud rank, percentile, hit@k vs random baseline
  * Mann-Whitney U with rank-biserial effect size and p-value (per cohort)
  * Bootstrap 95% CI on rank (1,000 resamples)
  * Within-cohort null permutation p-value of P(rank <= observed)
  * Aggregate hit@k and leave-one-fraud-out sensitivity

Writes:
  data/results/per_fraud_metrics.json
  data/results/aggregate_metrics.json
  data/results/per_fraud_summary.csv

This script is run ONCE against the frozen analysis spec. Whatever the
numbers say, that's the result.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.edgar import _strip_dashes
from engine.stats import (
    aggregate_hit_rates,
    bootstrap_rank_ci,
    leave_one_fraud_out,
    mann_whitney_fraud_vs_peers,
    null_permutation_p,
    rank_fraud_in_cohort,
)


def _load_scores() -> dict[str, list[dict]]:
    """Group scores.csv rows by cohort."""
    path = REPO_ROOT / "data/results/scores.csv"
    by_cohort: dict[str, list[dict]] = defaultdict(list)
    with path.open() as f:
        for row in csv.DictReader(f):
            by_cohort[row["cohort_id"]].append(row)
    return by_cohort


def _load_per_sent(ticker: str, accession: str) -> np.ndarray:
    path = REPO_ROOT / f"data/processed/per_sentence/{ticker}__{_strip_dashes(accession)}.npy"
    if not path.exists():
        return np.zeros((0,), dtype=np.float32)
    return np.load(path).astype(np.float32)


def main() -> int:
    by_cohort = _load_scores()
    if not by_cohort:
        print("FAIL: data/results/scores.csv missing or empty.")
        return 1

    per_fraud_results: list[dict] = []
    rank_results = []
    for ticker, rows in sorted(by_cohort.items()):
        fraud_rows = [r for r in rows if r["fraud_or_peer"] == "fraud"]
        peer_rows = [r for r in rows if r["fraud_or_peer"] == "peer"]
        if not fraud_rows or not peer_rows:
            print(f"[{ticker}] missing fraud or peer rows; skipping")
            continue
        fraud_row = fraud_rows[0]
        fraud_score = float(fraud_row["score_mean"])
        peer_scores = [float(r["score_mean"]) for r in peer_rows]

        rank = rank_fraud_in_cohort(ticker, fraud_score, peer_scores)
        rank_results.append(rank)

        # Mann-Whitney on per-sentence reconstruction errors
        fraud_per_sent = _load_per_sent(ticker, fraud_row["accession"])
        peer_per_sent = np.concatenate(
            [_load_per_sent(ticker, r["accession"]) for r in peer_rows] or [np.zeros((0,), dtype=np.float32)]
        )
        mw = mann_whitney_fraud_vs_peers(ticker, fraud_per_sent, peer_per_sent)
        ci = bootstrap_rank_ci(ticker, fraud_score, peer_scores, n_bootstrap=1000)
        nullp = null_permutation_p(ticker, fraud_score, peer_scores, n_permutations=1000)

        per_fraud_results.append({
            "ticker": ticker,
            "n_total": rank.n_total,
            "fraud_score": rank.fraud_score,
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
            "boot_lower_95": ci.lower_95,
            "boot_upper_95": ci.upper_95,
            "null_p_le_observed": nullp.p_le_observed,
        })

    if not rank_results:
        print("FAIL: no cohorts produced rank results.")
        return 1

    aggregate = aggregate_hit_rates(rank_results)
    lofo = leave_one_fraud_out(rank_results)

    (REPO_ROOT / "data/results").mkdir(parents=True, exist_ok=True)
    pf_path = REPO_ROOT / "data/results/per_fraud_metrics.json"
    pf_path.write_text(json.dumps({"per_fraud": per_fraud_results}, indent=2) + "\n")
    print(f"Wrote {pf_path}")

    agg_path = REPO_ROOT / "data/results/aggregate_metrics.json"
    agg_path.write_text(json.dumps({
        "aggregate": aggregate,
        "leave_one_fraud_out": [
            {"removed": ticker, "aggregate": metrics} for ticker, metrics in lofo
        ],
    }, indent=2) + "\n")
    print(f"Wrote {agg_path}")

    summary_path = REPO_ROOT / "data/results/per_fraud_summary.csv"
    with summary_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "ticker", "n_total", "rank", "percentile",
            "boot_lower_95", "boot_upper_95",
            "mw_p", "mw_effect", "null_p_le_observed",
        ])
        for r in per_fraud_results:
            w.writerow([
                r["ticker"], r["n_total"], r["fraud_rank"],
                f"{r['fraud_percentile']:.1f}",
                r["boot_lower_95"], r["boot_upper_95"],
                f"{r['mw_p']:.4g}", f"{r['mw_effect_rank_biserial']:.3f}",
                f"{r['null_p_le_observed']:.3f}",
            ])
    print(f"Wrote {summary_path}")

    print("\n=== Per-fraud rank summary ===")
    for r in per_fraud_results:
        print(
            f"  {r['ticker']:<6} rank={r['fraud_rank']:>2}/{r['n_total']:<2}  "
            f"pct={r['fraud_percentile']:>5.1f}  "
            f"CI=[{int(r['boot_lower_95'])},{int(r['boot_upper_95'])}]  "
            f"MW p={r['mw_p']:.4g} effect={r['mw_effect_rank_biserial']:+.2f}  "
            f"null p={r['null_p_le_observed']:.3f}"
        )
    print(f"\n=== Aggregate ===")
    for k, v in aggregate.items():
        print(f"  {k:<22} {v:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
