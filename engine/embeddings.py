"""MiniLM sentence embeddings with on-disk caching.

We use ``sentence-transformers/all-MiniLM-L6-v2`` (384-dim) as specified in
``analysis_spec.md``. Embeddings are cached at the filing level under
``data/processed/embeddings/<accession_nodash>.npz`` keyed by
``(filing_id, model_name, sentence_idx)``.

The cache is a numpy ``.npz`` with two arrays:
  * ``embeddings`` — shape (n_sentences, 384), float32
  * ``sentences``  — shape (n_sentences,), variable-length unicode

This module is imported only by Phase 3+; importing it requires
``sentence-transformers`` (which pulls torch) — so it is safe to keep imports
local. Phases 0-2 must remain importable without torch.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
EMBEDDING_CACHE_DIR = Path("data/processed/embeddings")


@dataclass
class FilingEmbeddings:
    accession: str
    model_name: str
    sentences: list[str]
    embeddings: np.ndarray  # (n_sentences, 384)

    @property
    def n_sentences(self) -> int:
        return self.embeddings.shape[0]


def _cache_path(accession: str, model_name: str) -> Path:
    model_hash = hashlib.sha1(model_name.encode()).hexdigest()[:10]
    safe_acc = accession.replace("-", "")
    return EMBEDDING_CACHE_DIR / f"{safe_acc}__{model_hash}.npz"


def _save(path: Path, sentences: list[str], embeddings: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sent_arr = np.array(sentences, dtype=object)
    np.savez_compressed(path, embeddings=embeddings.astype(np.float32), sentences=sent_arr)


def _load(path: Path) -> tuple[list[str], np.ndarray]:
    data = np.load(path, allow_pickle=True)
    return list(data["sentences"]), data["embeddings"].astype(np.float32)


class EmbeddingEngine:
    """Wrap a sentence-transformers model and provide cached batched encoding.

    Model loading is lazy: instantiating this class does NOT load the model
    until ``encode`` is first called.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL, *, device: str | None = None) -> None:
        self.model_name = model_name
        self._device = device
        self._model = None  # lazy

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        # Local import: sentence-transformers is a Phase-3+ dep.
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self.model_name, device=self._device)

    def encode_filing(
        self,
        accession: str,
        sentences: list[str],
        *,
        batch_size: int = 64,
        force: bool = False,
    ) -> FilingEmbeddings:
        """Encode an entire filing's sentences, hitting the on-disk cache when present."""
        path = _cache_path(accession, self.model_name)
        if path.exists() and not force:
            cached_sentences, cached_emb = _load(path)
            # If sentence list matches, use cache. Otherwise re-encode.
            if cached_sentences == sentences:
                return FilingEmbeddings(
                    accession=accession,
                    model_name=self.model_name,
                    sentences=cached_sentences,
                    embeddings=cached_emb,
                )

        self._ensure_model()
        assert self._model is not None
        emb = self._model.encode(
            sentences,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=False,
        ).astype(np.float32)
        _save(path, sentences, emb)
        return FilingEmbeddings(
            accession=accession,
            model_name=self.model_name,
            sentences=sentences,
            embeddings=emb,
        )

    def encode_batch(
        self,
        items: list[tuple[str, list[str]]],
        *,
        batch_size: int = 64,
        force: bool = False,
    ) -> list[FilingEmbeddings]:
        return [self.encode_filing(acc, sents, batch_size=batch_size, force=force)
                for acc, sents in items]
