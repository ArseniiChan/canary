"""Tests for engine/scoring.py."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

torch = pytest.importorskip("torch")

from engine.autoencoder import EMBEDDING_DIM, CanaryAutoencoder  # noqa: E402
from engine.scoring import per_sentence_recon_error, score_filing  # noqa: E402


def test_per_sentence_recon_error_shape():
    model = CanaryAutoencoder()
    x = np.random.default_rng(0).standard_normal((20, EMBEDDING_DIM)).astype(np.float32)
    err = per_sentence_recon_error(model, x)
    assert err.shape == (20,)
    assert (err >= 0).all()


def test_per_sentence_recon_error_zero_for_perfect_recon():
    """If the model returns exactly its input (identity), reconstruction error is zero."""
    rng = np.random.default_rng(0)
    x = rng.standard_normal((5, EMBEDDING_DIM)).astype(np.float32)

    class IdentityModel(CanaryAutoencoder):
        def forward(self, t):
            return t

    err = per_sentence_recon_error(IdentityModel(), x)
    assert np.allclose(err, 0.0, atol=1e-6)


def test_score_filing_aggregations():
    model = CanaryAutoencoder()
    x = np.random.default_rng(0).standard_normal((50, EMBEDDING_DIM)).astype(np.float32)
    res = score_filing("acc-1", x, model)
    assert res.n_sentences == 50
    assert res.mean_recon_error >= 0
    assert res.max_recon_error >= res.mean_recon_error
    # trimmed mean should be between min and max
    per_sent_min = float(res.per_sentence.min())
    per_sent_max = float(res.per_sentence.max())
    assert per_sent_min <= res.trimmed_mean_recon_error <= per_sent_max
