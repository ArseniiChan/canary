"""Phase 6 (post-hoc): figures comparing the autoencoder against the TF-IDF
trivial baseline, and showing the post-hoc entity-masking ablation.

Outputs:
  reports/figures/ae_vs_tfidf_rank.png       per-fraud rank: AE vs TF-IDF
  reports/figures/ae_vs_tfidf_mw.png         per-cohort Mann-Whitney p (log)
  reports/figures/entity_masking_posthoc.png orig vs masked rank by cohort
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
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


def load_per_fraud(path: Path) -> list[dict]:
    return json.loads(path.read_text())["per_fraud"]


def fig_rank_compare(ae: list[dict], tf: list[dict]) -> None:
    tf_by_t = {r["ticker"]: r for r in tf}
    tickers = [r["ticker"] for r in ae]
    ae_ranks = [r["fraud_rank"] for r in ae]
    tf_ranks = [tf_by_t[t]["fraud_rank"] for t in tickers]
    n_total = [r["n_total"] for r in ae]
    expected = [(n + 1) / 2 for n in n_total]
    x = np.arange(len(tickers))
    fig, ax = plt.subplots()
    ax.bar(x - 0.22, ae_ranks, width=0.22, label="Autoencoder", color="#d4a017")
    ax.bar(x,        tf_ranks, width=0.22, label="TF-IDF + SVD32", color="#1f77b4")
    ax.bar(x + 0.22, expected, width=0.22, label="Expected (random)", color="#999")
    ax.set_xticks(x)
    ax.set_xticklabels(tickers)
    ax.set_ylabel("Rank within cohort (1 = highest reconstruction error)")
    ax.set_title("Per-fraud rank: autoencoder vs TF-IDF + SVD32 baseline")
    ax.invert_yaxis()
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "ae_vs_tfidf_rank.png")
    plt.close(fig)


def fig_mw_compare(ae: list[dict], tf: list[dict]) -> None:
    tf_by_t = {r["ticker"]: r for r in tf}
    tickers = [r["ticker"] for r in ae]
    ae_p = [max(r["mw_p"], 1e-300) for r in ae]
    tf_p = [max(tf_by_t[t]["mw_p"], 1e-300) for t in tickers]
    x = np.arange(len(tickers))
    fig, ax = plt.subplots()
    ax.bar(x - 0.18, [-np.log10(p) for p in ae_p], width=0.36, label="Autoencoder", color="#d4a017")
    ax.bar(x + 0.18, [-np.log10(p) for p in tf_p], width=0.36, label="TF-IDF + SVD32", color="#1f77b4")
    ax.axhline(-np.log10(0.05), color="#888", linestyle="--", label="p = 0.05")
    ax.set_xticks(x)
    ax.set_xticklabels(tickers)
    ax.set_ylabel("-log10(p)   Mann-Whitney U, fraud > peers")
    ax.set_title("Per-cohort Mann-Whitney p — autoencoder vs trivial baseline")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "ae_vs_tfidf_mw.png")
    plt.close(fig)


def fig_entity_masking(ent: list[dict]) -> None:
    tickers = [r["ticker"] for r in ent]
    orig = [r["original_rank"] for r in ent]
    masked = [r["masked_rank"] for r in ent]
    n_total = [r["n_total_in_cohort"] for r in ent]
    x = np.arange(len(tickers))
    fig, ax = plt.subplots()
    ax.bar(x - 0.18, orig,   width=0.36, label="Original rank", color="#d4a017")
    ax.bar(x + 0.18, masked, width=0.36, label="Entity-masked rank (post-hoc)", color="#7c4dff")
    for xi, n in zip(x, n_total):
        ax.text(xi, max(orig[xi], masked[xi]) + 0.4, f"of {n}", ha="center", fontsize=9, color="#555")
    ax.set_xticks(x)
    ax.set_xticklabels(tickers)
    ax.set_ylabel("Rank within cohort")
    ax.set_title("Post-hoc entity-masking — original vs masked autoencoder rank")
    ax.invert_yaxis()
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "entity_masking_posthoc.png")
    plt.close(fig)


def main() -> int:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    ae = load_per_fraud(RES_DIR / "per_fraud_metrics.json")
    tf = load_per_fraud(RES_DIR / "per_fraud_metrics_tfidf.json")
    ent = json.loads((RES_DIR / "entity_masking_posthoc.json").read_text())["per_fraud"]
    fig_rank_compare(ae, tf)
    fig_mw_compare(ae, tf)
    fig_entity_masking(ent)
    print(f"Wrote 3 post-hoc figures to {FIG_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
