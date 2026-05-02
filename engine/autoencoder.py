"""PyTorch autoencoder over MiniLM sentence embeddings, with leave-one-cohort-out
+ time-controlled training as specified in ``analysis_spec.md``.

Architecture (frozen): 384 -> 128 -> 32 -> 128 -> 384, ReLU, MSE loss, Adam(lr=1e-3),
batch 16, 200 epochs with early stopping on a 20% validation split. All RNGs
seeded.

Training contract (LOCO + time-controlled):
  * For each fraud cohort C, the training set comprises sentences from CLEAN PEER
    filings of cohorts OTHER THAN C, AND whose filing_date <= the fraud's
    filing_date. The fraud's own filing AND any peer in cohort C are NEVER in
    the training set.
  * Per-filing sentence cap of 100 during training (uniform sample if more).

Inference: a model is loaded and used to score sentences from any filing
(including the held-out fraud + cohort peers); the per-sentence reconstruction
errors and the filing-level mean are returned.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

EMBEDDING_DIM = 384
HIDDEN_DIM = 128
BOTTLENECK_DIM = 32
SENTENCE_CAP = 100  # per-filing during training
DEFAULT_SEED = 42

MODEL_DIR = Path("data/processed/models")


@dataclass
class TrainingResult:
    cohort_id: str
    n_train_filings: int
    n_train_sentences: int
    n_val_sentences: int
    final_train_loss: float
    final_val_loss: float
    best_val_loss: float
    best_epoch: int
    n_epochs_run: int
    model_path: str


class CanaryAutoencoder(nn.Module):
    """384 -> 128 -> 32 -> 128 -> 384, ReLU, sigmoid not used (linear output)."""

    def __init__(
        self,
        in_dim: int = EMBEDDING_DIM,
        hidden_dim: int = HIDDEN_DIM,
        bottleneck_dim: int = BOTTLENECK_DIM,
    ) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, bottleneck_dim),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(bottleneck_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, in_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(x))


def _seed_all(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _sample_sentences(
    embeddings: np.ndarray,
    n: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Uniformly sample up to ``n`` rows from ``embeddings`` without replacement."""
    if embeddings.shape[0] <= n:
        return embeddings
    idx = rng.choice(embeddings.shape[0], size=n, replace=False)
    return embeddings[np.sort(idx)]


def build_training_matrix(
    filing_embeddings: list[tuple[str, np.ndarray]],
    *,
    sentence_cap: int = SENTENCE_CAP,
    seed: int = DEFAULT_SEED,
) -> np.ndarray:
    """Stack training rows from many filings, applying a per-filing sentence cap."""
    rng = np.random.default_rng(seed)
    parts = [_sample_sentences(emb, sentence_cap, rng) for _, emb in filing_embeddings]
    if not parts:
        return np.zeros((0, EMBEDDING_DIM), dtype=np.float32)
    return np.concatenate(parts, axis=0).astype(np.float32)


def train_cohort_autoencoder(
    cohort_id: str,
    train_filings: list[tuple[str, np.ndarray]],
    *,
    sentence_cap: int = SENTENCE_CAP,
    epochs: int = 200,
    batch_size: int = 16,
    lr: float = 1e-3,
    val_split: float = 0.20,
    seed: int = DEFAULT_SEED,
    early_stop_patience: int = 20,
    device: str | None = None,
    out_dir: Path = MODEL_DIR,
) -> TrainingResult:
    """Train one autoencoder for the given cohort under LOCO + time-controlled inputs.

    ``train_filings`` is a list of ``(accession, embeddings)`` tuples where
    ``embeddings`` is a (n_sentences, 384) ``np.ndarray``. The caller is
    responsible for ensuring those filings satisfy the LOCO + time-controlled
    constraints (i.e. they are clean peers from OTHER cohorts and dated <= the
    fraud's filing date).
    """
    if not train_filings:
        raise ValueError(f"cohort {cohort_id}: no training filings supplied")

    _seed_all(seed)
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    out_dir.mkdir(parents=True, exist_ok=True)

    X = build_training_matrix(train_filings, sentence_cap=sentence_cap, seed=seed)
    if X.shape[0] < 32:
        raise ValueError(
            f"cohort {cohort_id}: training matrix only {X.shape[0]} rows — too few to fit"
        )

    rng = np.random.default_rng(seed)
    perm = rng.permutation(X.shape[0])
    n_val = max(1, int(round(X.shape[0] * val_split)))
    val_idx = perm[:n_val]
    train_idx = perm[n_val:]

    X_train = torch.from_numpy(X[train_idx]).to(device)
    X_val = torch.from_numpy(X[val_idx]).to(device)
    train_loader = DataLoader(TensorDataset(X_train), batch_size=batch_size, shuffle=True)

    model = CanaryAutoencoder().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    best_val = float("inf")
    best_epoch = -1
    best_state: dict | None = None
    epochs_run = 0
    final_train_loss = float("nan")
    final_val_loss = float("nan")
    patience_counter = 0

    for epoch in range(epochs):
        epochs_run = epoch + 1
        model.train()
        total = 0.0
        n_batches = 0
        for (batch,) in train_loader:
            opt.zero_grad()
            recon = model(batch)
            loss = loss_fn(recon, batch)
            loss.backward()
            opt.step()
            total += loss.item()
            n_batches += 1
        train_loss = total / max(n_batches, 1)

        model.eval()
        with torch.no_grad():
            val_loss = loss_fn(model(X_val), X_val).item()

        final_train_loss = train_loss
        final_val_loss = val_loss

        if val_loss < best_val - 1e-6:
            best_val = val_loss
            best_epoch = epoch
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= early_stop_patience:
                break

    if best_state is not None:
        model.load_state_dict(best_state)

    model_path = out_dir / f"{cohort_id}.pt"
    torch.save({
        "cohort_id": cohort_id,
        "state_dict": model.state_dict(),
        "config": {
            "embedding_dim": EMBEDDING_DIM,
            "hidden_dim": HIDDEN_DIM,
            "bottleneck_dim": BOTTLENECK_DIM,
            "sentence_cap": sentence_cap,
            "epochs": epochs,
            "batch_size": batch_size,
            "lr": lr,
            "val_split": val_split,
            "seed": seed,
        },
        "training_filings": [acc for acc, _ in train_filings],
    }, model_path)

    return TrainingResult(
        cohort_id=cohort_id,
        n_train_filings=len(train_filings),
        n_train_sentences=int(X_train.shape[0]),
        n_val_sentences=int(X_val.shape[0]),
        final_train_loss=float(final_train_loss),
        final_val_loss=float(final_val_loss),
        best_val_loss=float(best_val),
        best_epoch=int(best_epoch),
        n_epochs_run=int(epochs_run),
        model_path=str(model_path),
    )


def load_cohort_autoencoder(model_path: Path | str, *, device: str | None = None) -> CanaryAutoencoder:
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    chk = torch.load(Path(model_path), map_location=device, weights_only=False)
    model = CanaryAutoencoder().to(device)
    model.load_state_dict(chk["state_dict"])
    model.eval()
    return model
