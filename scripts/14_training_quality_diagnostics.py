"""Council-recommended training-quality diagnostics — proves the models work.

Three figures + one stdout summary:

  reports/figures/recon_error_hist_per_cohort.png
      Per-cohort histogram of per-sentence reconstruction error,
      fraud sentences vs peer sentences. Shows visually whether the AE
      can separate the two distributions per cohort.

  reports/figures/noise_sanity_check.png
      Bar chart: mean reconstruction error on (a) real fraud sentences,
      (b) real peer sentences, (c) random Gaussian noise vectors fed to
      the same autoencoder. Noise should produce dramatically higher
      reconstruction error — proves the AE actually learned something.

  reports/figures/dynamic_range_per_cohort.png
      Per-cohort scatter: filing-level mean reconstruction error,
      fraud (red star) vs peer (gray dots). Shows the within-cohort
      dynamic range that the rank metric is built on.

Stdout: numerical summary table.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.autoencoder import EMBEDDING_DIM, MODEL_DIR, load_cohort_autoencoder
from engine.scoring import per_sentence_recon_error

FIG_DIR = REPO_ROOT / "reports/figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
PER_SENTENCE_DIR = REPO_ROOT / "data/processed/per_sentence"

COHORT_IDS = ["HRC", "LEH", "TYC", "VRX", "WCOM"]

plt.rcParams.update({
    "figure.dpi": 144,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.size": 10,
})


def load_per_sentence(cohort: str, accession: str) -> np.ndarray:
    p = PER_SENTENCE_DIR / f"{cohort}__{accession.replace('-', '')}.npy"
    if not p.exists():
        return np.zeros((0,), dtype=np.float32)
    return np.load(p)


def fig_recon_error_hist(scores: list[dict]) -> None:
    fig, axes = plt.subplots(1, 5, figsize=(18, 3.6), sharey=True)
    for ax, cid in zip(axes, COHORT_IDS):
        rows = [r for r in scores if r["cohort_id"] == cid]
        fraud_arr = []
        peer_arr = []
        for r in rows:
            arr = load_per_sentence(cid, r["accession"])
            if r["fraud_or_peer"] == "fraud":
                fraud_arr = arr
            else:
                peer_arr.append(arr)
        if not len(fraud_arr) or not peer_arr:
            ax.set_title(f"{cid}: missing data")
            continue
        peer_concat = np.concatenate(peer_arr)
        # log-scale per-sentence errors are roughly log-normal
        bins = np.linspace(min(fraud_arr.min(), peer_concat.min()),
                           max(fraud_arr.max(), peer_concat.max()), 50)
        ax.hist(peer_concat, bins=bins, density=True, alpha=0.55, color="#777", label=f"peers n={peer_concat.size}")
        ax.hist(fraud_arr,   bins=bins, density=True, alpha=0.65, color="#d4a017", label=f"fraud n={fraud_arr.size}")
        ax.set_title(cid)
        ax.set_xlabel("per-sentence MSE")
        if cid == COHORT_IDS[0]:
            ax.set_ylabel("density")
        ax.legend(fontsize=8, loc="upper right")
    fig.suptitle("Per-cohort per-sentence reconstruction-error distributions", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "recon_error_hist_per_cohort.png", bbox_inches="tight")
    plt.close(fig)


def fig_noise_sanity(scores: list[dict]) -> None:
    """Feed N(0,1) random vectors of the same dim to each cohort autoencoder
    and compare reconstruction error against real fraud + peer sentences."""
    rng = np.random.default_rng(42)
    n_noise_samples = 1000
    means_real_fraud, means_real_peer, means_noise = [], [], []
    means_unitnorm_noise = []
    for cid in COHORT_IDS:
        model_path = MODEL_DIR / f"{cid}.pt"
        if not model_path.exists():
            continue
        model = load_cohort_autoencoder(model_path)
        # Fraud + peer per-sentence errors from existing artefacts
        rows = [r for r in scores if r["cohort_id"] == cid]
        fraud_err = next(load_per_sentence(cid, r["accession"]) for r in rows if r["fraud_or_peer"] == "fraud")
        peer_err  = np.concatenate([load_per_sentence(cid, r["accession"]) for r in rows if r["fraud_or_peer"] == "peer"])
        means_real_fraud.append(fraud_err.mean())
        means_real_peer.append(peer_err.mean())
        # Random Gaussian noise
        noise_raw = rng.standard_normal((n_noise_samples, EMBEDDING_DIM)).astype(np.float32)
        noise_err = per_sentence_recon_error(model, noise_raw)
        means_noise.append(noise_err.mean())
        # Unit-normalised noise (closer to actual MiniLM embedding magnitude)
        norm = noise_raw / np.linalg.norm(noise_raw, axis=1, keepdims=True)
        unit_err = per_sentence_recon_error(model, norm.astype(np.float32))
        means_unitnorm_noise.append(unit_err.mean())

    x = np.arange(len(COHORT_IDS))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(x - 0.30, means_real_peer,      width=0.18, label="real peer sentences",   color="#777")
    ax.bar(x - 0.10, means_real_fraud,     width=0.18, label="real fraud sentences",  color="#d4a017")
    ax.bar(x + 0.10, means_unitnorm_noise, width=0.18, label="unit-norm Gaussian noise", color="#1f77b4")
    ax.bar(x + 0.30, means_noise,          width=0.18, label="raw N(0,1) noise",      color="#8b0000")
    ax.set_xticks(x); ax.set_xticklabels(COHORT_IDS)
    ax.set_ylabel("mean per-sentence reconstruction error (MSE)")
    ax.set_title("Noise sanity check — out-of-distribution input collapses the model")
    ax.set_yscale("log")
    ax.legend(fontsize=9, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "noise_sanity_check.png", bbox_inches="tight")
    plt.close(fig)

    print("\nNoise sanity check (mean per-sentence MSE):")
    print(f"{'cohort':<6} {'real peer':>14} {'real fraud':>14} {'unit-noise':>14} {'raw N(0,1)':>14} {'noise/real':>14}")
    print("-" * 86)
    for i, cid in enumerate(COHORT_IDS):
        ratio = means_unitnorm_noise[i] / means_real_peer[i] if means_real_peer[i] > 0 else float("nan")
        print(f"{cid:<6} {means_real_peer[i]:>14.6f} {means_real_fraud[i]:>14.6f} "
              f"{means_unitnorm_noise[i]:>14.6f} {means_noise[i]:>14.6f} {ratio:>14.1f}x")


def fig_dynamic_range(scores: list[dict]) -> None:
    """Per-cohort scatter of filing-level mean recon error: fraud vs peers."""
    fig, ax = plt.subplots(figsize=(10, 4))
    x_labels = []
    for i, cid in enumerate(COHORT_IDS):
        rows = [r for r in scores if r["cohort_id"] == cid]
        fraud = next(float(r["score_mean"]) for r in rows if r["fraud_or_peer"] == "fraud")
        peers = [float(r["score_mean"]) for r in rows if r["fraud_or_peer"] == "peer"]
        ax.scatter([i] * len(peers), peers, color="#999", alpha=0.7, s=30, label="peer" if i == 0 else None)
        ax.scatter([i], [fraud], color="#d4a017", marker="*", s=200,
                   edgecolor="black", linewidth=0.8, label="fraud" if i == 0 else None)
        x_labels.append(cid)
    ax.set_xticks(range(len(COHORT_IDS)))
    ax.set_xticklabels(x_labels)
    ax.set_ylabel("filing-level mean per-sentence MSE")
    ax.set_title("Filing-level reconstruction error per cohort — fraud (★) vs peers (•)")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "dynamic_range_per_cohort.png", bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    with (REPO_ROOT / "data/results/scores.csv").open() as f:
        scores = list(csv.DictReader(f))

    fig_recon_error_hist(scores)
    fig_noise_sanity(scores)
    fig_dynamic_range(scores)
    print(f"\nWrote 3 diagnostics figures to {FIG_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
