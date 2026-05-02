"""Tests for engine/autoencoder.py.

These tests skip themselves when torch is not installed so the suite still
runs in environments where Phases 0-2 deps are present but torch is not.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

torch = pytest.importorskip("torch")

from engine.autoencoder import (  # noqa: E402
    BOTTLENECK_DIM,
    EMBEDDING_DIM,
    HIDDEN_DIM,
    CanaryAutoencoder,
    build_training_matrix,
    train_cohort_autoencoder,
)


def test_canary_autoencoder_shape_roundtrip():
    model = CanaryAutoencoder()
    x = torch.randn(8, EMBEDDING_DIM)
    out = model(x)
    assert out.shape == x.shape


def test_canary_autoencoder_bottleneck_compresses():
    model = CanaryAutoencoder()
    x = torch.randn(2, EMBEDDING_DIM)
    z = model.encoder(x)
    assert z.shape == (2, BOTTLENECK_DIM)


def test_build_training_matrix_caps_per_filing():
    rng = np.random.default_rng(0)
    f1 = ("acc-1", rng.standard_normal((300, EMBEDDING_DIM)).astype(np.float32))
    f2 = ("acc-2", rng.standard_normal((50, EMBEDDING_DIM)).astype(np.float32))
    X = build_training_matrix([f1, f2], sentence_cap=100, seed=42)
    # Capped per filing: 100 + 50 = 150 rows
    assert X.shape == (150, EMBEDDING_DIM)


def test_train_cohort_autoencoder_smoke(tmp_path: Path):
    """Tiny smoke test: 2 filings, 100 sentences each, 2 epochs."""
    rng = np.random.default_rng(0)
    filings = [(f"acc-{i}", rng.standard_normal((100, EMBEDDING_DIM)).astype(np.float32))
               for i in range(2)]
    res = train_cohort_autoencoder(
        "TEST",
        filings,
        sentence_cap=100,
        epochs=3,
        batch_size=32,
        early_stop_patience=10,
        out_dir=tmp_path,
    )
    assert res.cohort_id == "TEST"
    assert res.n_train_filings == 2
    assert res.final_train_loss >= 0
    assert (tmp_path / "TEST.pt").exists()
