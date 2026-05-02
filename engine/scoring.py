"""Filing-level reconstruction-error scoring.

For each filing's sentence embeddings, compute per-sentence MSE reconstruction
error against a trained autoencoder, then aggregate to a filing-level score.

Primary aggregation (from analysis_spec.md): **mean** per-sentence error.
Ablation aggregations (descriptive only, appendix): trimmed-mean@5%, max.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from engine.autoencoder import CanaryAutoencoder


@dataclass
class FilingScore:
    accession: str
    n_sentences: int
    mean_recon_error: float
    trimmed_mean_recon_error: float  # 5% trim, ablation
    max_recon_error: float
    per_sentence: np.ndarray  # (n_sentences,)


def per_sentence_recon_error(
    model: CanaryAutoencoder,
    embeddings: np.ndarray,
    *,
    device: str | None = None,
    batch_size: int = 256,
) -> np.ndarray:
    """Return per-sentence MSE reconstruction error: shape (n_sentences,)."""
    if embeddings.size == 0:
        return np.zeros((0,), dtype=np.float32)
    device = device or next(model.parameters()).device.type
    model.eval()
    errors: list[np.ndarray] = []
    with torch.no_grad():
        for i in range(0, embeddings.shape[0], batch_size):
            batch = torch.from_numpy(embeddings[i : i + batch_size]).to(device)
            recon = model(batch)
            err = ((recon - batch) ** 2).mean(dim=1).detach().cpu().numpy()
            errors.append(err)
    return np.concatenate(errors, axis=0).astype(np.float32)


def score_filing(
    accession: str,
    embeddings: np.ndarray,
    model: CanaryAutoencoder,
    *,
    trim_frac: float = 0.05,
) -> FilingScore:
    per_sent = per_sentence_recon_error(model, embeddings)
    if per_sent.size == 0:
        return FilingScore(accession, 0, float("nan"), float("nan"), float("nan"), per_sent)
    mean = float(per_sent.mean())
    sorted_err = np.sort(per_sent)
    k = int(round(len(sorted_err) * trim_frac))
    trimmed = sorted_err[k : len(sorted_err) - k] if len(sorted_err) > 2 * k else sorted_err
    trimmed_mean = float(trimmed.mean()) if len(trimmed) > 0 else mean
    mx = float(per_sent.max())
    return FilingScore(
        accession=accession,
        n_sentences=int(per_sent.shape[0]),
        mean_recon_error=mean,
        trimmed_mean_recon_error=trimmed_mean,
        max_recon_error=mx,
        per_sentence=per_sent,
    )
