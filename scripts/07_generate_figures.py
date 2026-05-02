"""Phase 6 — regenerate every report figure from data/results/.

Outputs (PNG, written to reports/figures/):
  per_fraud_rank.png        per-fraud rank with random-baseline reference line
  bootstrap_ci.png          per-fraud bootstrap 95% CI on rank
  mw_p_values.png           per-fraud Mann-Whitney p-values (log scale)
  hit_at_k.png              aggregate hit@k vs random baseline
  rank_distribution.png     histogram of fraud ranks across cohorts
  per_sentence_distribution.png   density plot: fraud vs peer per-sentence errors (Enron only)

This script is fully deterministic given data/results/ is present. Style:
  * matplotlib default with light tweaks (monospace numbers)
  * dpi=144, figsize=(8, 5)
  * one chart per file, saved as PNG
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # pure-file output, no display
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]

FIG_DIR = REPO_ROOT / "reports/figures"
RES_DIR = REPO_ROOT / "data/results"

plt.rcParams.update({
    "figure.dpi": 144,
    "figure.figsize": (8, 5),
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.size": 11,
})


def _load_per_fraud() -> list[dict]:
    return json.loads((RES_DIR / "per_fraud_metrics.json").read_text())["per_fraud"]


def _load_aggregate() -> dict:
    return json.loads((RES_DIR / "aggregate_metrics.json").read_text())


def fig_per_fraud_rank(rows: list[dict]) -> None:
    tickers = [r["ticker"] for r in rows]
    ranks = [r["fraud_rank"] for r in rows]
    n_totals = [r["n_total"] for r in rows]
    expected = [(n + 1) / 2 for n in n_totals]
    x = np.arange(len(tickers))
    fig, ax = plt.subplots()
    ax.bar(x - 0.18, ranks, width=0.36, label="Observed rank", color="#d4a017")
    ax.bar(x + 0.18, expected, width=0.36, label="Expected (random)", color="#999999")
    ax.set_xticks(x)
    ax.set_xticklabels(tickers)
    ax.set_ylabel("Rank within cohort (1 = highest reconstruction error)")
    ax.set_title("Per-fraud rank vs random-baseline expectation")
    ax.invert_yaxis()
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "per_fraud_rank.png")
    plt.close(fig)


def fig_bootstrap_ci(rows: list[dict]) -> None:
    tickers = [r["ticker"] for r in rows]
    ranks = [r["fraud_rank"] for r in rows]
    lower = [r["boot_lower_95"] for r in rows]
    upper = [r["boot_upper_95"] for r in rows]
    err_low = [ranks[i] - lower[i] for i in range(len(rows))]
    err_high = [upper[i] - ranks[i] for i in range(len(rows))]
    x = np.arange(len(tickers))
    fig, ax = plt.subplots()
    ax.errorbar(x, ranks, yerr=[err_low, err_high], fmt="o", color="#d4a017",
                ecolor="#444", elinewidth=1.5, capsize=4)
    ax.set_xticks(x)
    ax.set_xticklabels(tickers)
    ax.set_ylabel("Rank within cohort (1,000 bootstrap)")
    ax.set_title("Per-fraud rank with bootstrap 95% CI")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "bootstrap_ci.png")
    plt.close(fig)


def fig_mw_p(rows: list[dict]) -> None:
    tickers = [r["ticker"] for r in rows]
    pvals = [max(r["mw_p"], 1e-300) for r in rows]
    fig, ax = plt.subplots()
    bars = ax.bar(tickers, [-np.log10(p) for p in pvals], color="#d4a017")
    ax.axhline(-np.log10(0.05), color="#888", linestyle="--", label="p = 0.05")
    ax.set_ylabel("-log10(p)  (Mann-Whitney U, fraud > peers)")
    ax.set_title("Per-cohort Mann-Whitney U p-values")
    ax.legend()
    for b, p in zip(bars, pvals):
        ax.text(b.get_x() + b.get_width()/2, b.get_height(),
                f"{p:.2g}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "mw_p_values.png")
    plt.close(fig)


def fig_hit_at_k(agg: dict) -> None:
    a = agg["aggregate"]
    labels = ["hit@1", "hit@3", "hit@5"]
    observed = [a["hit_at_1"], a["hit_at_3"], a["hit_at_5"]]
    random = [a["random_hit_at_1"], a["random_hit_at_3"], a["random_hit_at_5"]]
    x = np.arange(len(labels))
    fig, ax = plt.subplots()
    ax.bar(x - 0.18, observed, width=0.36, label="Observed", color="#d4a017")
    ax.bar(x + 0.18, random, width=0.36, label="Random baseline", color="#999")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Aggregate hit rate")
    ax.set_title("Hit@k vs random baseline (averaged across cohorts)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "hit_at_k.png")
    plt.close(fig)


def fig_rank_distribution(rows: list[dict]) -> None:
    ranks = [r["fraud_rank"] for r in rows]
    fig, ax = plt.subplots()
    ax.hist(ranks, bins=range(1, max(ranks) + 2), color="#d4a017", edgecolor="black", align="left")
    ax.set_xlabel("Rank within cohort")
    ax.set_ylabel("Number of frauds")
    ax.set_title("Distribution of fraud ranks across cohorts")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "rank_distribution.png")
    plt.close(fig)


def main() -> int:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    rows = _load_per_fraud()
    agg = _load_aggregate()
    fig_per_fraud_rank(rows)
    fig_bootstrap_ci(rows)
    fig_mw_p(rows)
    fig_hit_at_k(agg)
    fig_rank_distribution(rows)
    print(f"Wrote 5 figures to {FIG_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
