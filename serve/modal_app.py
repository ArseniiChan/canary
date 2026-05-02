"""Modal-deployed inference API for the Canary dashboard's /scan page.

Deploys a small FastAPI app behind a Modal endpoint. Visitors POST a 10-K
filing (HTML, plain text, or raw MD&A text); the endpoint extracts MD&A,
embeds with MiniLM, scores against each of the 5 trained cohort
autoencoders, and returns where the input would rank within each cohort.

Local test:
    cd canary
    .venv/bin/pip install modal
    .venv/bin/python -m modal token new
    .venv/bin/python -m modal serve serve/modal_app.py
    # → URL printed; POST to /score for testing

Deploy:
    .venv/bin/python -m modal deploy serve/modal_app.py
    # → records URL; paste into dashboard/.env.local as NEXT_PUBLIC_CANARY_API
"""

from __future__ import annotations

import base64
import io
import sys
from pathlib import Path

import modal

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_NAME = "canary-inference"

# -- Container image ----------------------------------------------------------
# Bundle the engine module, the trained autoencoders, and scores.csv into the
# container so cold start doesn't touch network. MiniLM is downloaded once on
# first call and cached in the image's HF cache directory.
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "fastapi[standard]==0.115.0",
        "torch==2.4.0",
        "sentence-transformers==3.1.1",
        "numpy<2.0.0",
        "pandas==2.2.3",
        "scipy==1.14.1",
        "beautifulsoup4==4.12.3",
        "lxml==5.3.0",
    )
    .add_local_dir(
        str(REPO_ROOT / "engine"), remote_path="/root/engine"
    )
    .add_local_dir(
        str(REPO_ROOT / "data" / "processed" / "models"),
        remote_path="/root/models",
    )
    .add_local_file(
        str(REPO_ROOT / "data" / "results" / "scores.csv"),
        remote_path="/root/scores.csv",
    )
)

app = modal.App(APP_NAME, image=image)

# Five cohort tickers (Enron is excluded — no cohort model exists).
COHORTS = ["LEH", "WCOM", "TYC", "HRC", "VRX"]
# Largest real 10-K in the project corpus is ~6 MB and scores in <20s warm.
# At ~12 MB / ~280k sentences the embedder hits Modal's 180s container timeout,
# so the endpoint returns 500. Cap the upload at 8 MB to keep a comfortable
# margin, and short-circuit on sentence count (Phase 7 stress test, 2026-05-02).
MAX_FILE_BYTES = 8 * 1024 * 1024  # 8 MB
MAX_SENTENCES   = 10_000          # ~3-4x the largest real filing in the corpus


@app.cls(
    cpu=2,
    memory=4096,
    timeout=180,
    scaledown_window=300,  # keep warm for 5 min
    min_containers=0,
)
class Inference:
    """Loads MiniLM + 5 cohort autoencoders once per container."""

    @modal.enter()
    def load(self) -> None:
        # Make engine/ importable
        sys.path.insert(0, "/root")

        from engine.autoencoder import load_cohort_autoencoder
        from engine.embeddings import EmbeddingEngine

        self.encoder = EmbeddingEngine()
        # Force model load now (avoids cold-start penalty on first request)
        self.encoder._ensure_model()

        self.models = {
            ticker: load_cohort_autoencoder(f"/root/models/{ticker}.pt")
            for ticker in COHORTS
        }

        # Pre-load the score table so we can compute percentiles per cohort.
        import csv
        from collections import defaultdict

        self.scores_by_cohort: dict[str, list[dict]] = defaultdict(list)
        with open("/root/scores.csv") as f:
            for row in csv.DictReader(f):
                cohort = row["cohort_id"]
                self.scores_by_cohort[cohort].append({
                    "kind": row["fraud_or_peer"],
                    "score": float(row["score_mean"]),
                    "accession": row["accession"],
                    "filing_date": row["filing_date"],
                })

    def _percentile_in_cohort(self, ticker: str, score: float) -> dict:
        """Where would this score rank if dropped into the cohort?"""
        peers_and_fraud = self.scores_by_cohort.get(ticker, [])
        all_scores = [r["score"] for r in peers_and_fraud]
        n = len(all_scores)
        # Rank: 1 = highest reconstruction error; ours sits at this position.
        rank = sum(1 for s in all_scores if s > score) + 1
        # Percentile of "ours is more anomalous than X%"
        pct = 100.0 * sum(1 for s in all_scores if s < score) / n if n else 0.0
        return {
            "cohort_id": ticker,
            "rank_if_added": rank,
            "n_after_add": n + 1,
            "percentile_within_cohort": pct,
            "fraud_score": next(
                (r["score"] for r in peers_and_fraud if r["kind"] == "fraud"),
                None,
            ),
        }

    @modal.method()
    def score(self, *, body: bytes, filename: str | None) -> dict:
        sys.path.insert(0, "/root")

        from engine.parsing import extract_mdna, split_sentences
        from engine.scoring import score_filing

        # Decide: raw text, HTML, or already-extracted MD&A
        decoded = body.decode("utf-8", errors="replace")
        accession = filename or "uploaded"
        primary_doc = filename or "input.txt"

        # If body looks like MD&A directly (not a full 10-K), wrap it so the
        # extractor can find Item 7 boundaries — but if it's plain MD&A
        # without those markers, fall back to using the body directly.
        ext = extract_mdna(body, accession=accession, primary_document=primary_doc)
        if ext.success:
            body_text = ext.text
            extraction_method = ext.method
            extraction_chars = ext.char_count
            extraction_note = "extracted from filing"
        else:
            body_text = decoded
            extraction_method = "raw_text_fallback"
            extraction_chars = len(decoded)
            extraction_note = (
                "no Item 7 boundaries found — treating input as raw MD&A text"
            )

        sentences = split_sentences(body_text)
        if len(sentences) < 5:
            return {
                "ok": False,
                "error": f"only {len(sentences)} sentence(s) found — need at least 5",
                "extraction_method": extraction_method,
                "extraction_chars": extraction_chars,
            }
        if len(sentences) > MAX_SENTENCES:
            return {
                "ok": False,
                "error": (
                    f"input produces {len(sentences):,} sentences — exceeds "
                    f"the {MAX_SENTENCES:,} sentence cap (would not finish "
                    f"within the request timeout). Trim the input or paste "
                    f"only the MD&A (Item 7) section."
                ),
                "extraction_method": extraction_method,
                "extraction_chars": extraction_chars,
                "n_sentences_seen": len(sentences),
            }

        fe = self.encoder.encode_filing("uploaded", sentences)

        per_cohort = []
        for ticker in COHORTS:
            sc = score_filing("uploaded", fe.embeddings, self.models[ticker])
            stats = self._percentile_in_cohort(ticker, sc.mean_recon_error)
            per_cohort.append({
                **stats,
                "score_mean": sc.mean_recon_error,
                "score_trimmed_mean": sc.trimmed_mean_recon_error,
                "score_max": sc.max_recon_error,
            })

        return {
            "ok": True,
            "extraction": {
                "method": extraction_method,
                "chars": extraction_chars,
                "note": extraction_note,
            },
            "n_sentences": len(sentences),
            "per_cohort": per_cohort,
        }


# -- HTTP endpoint ------------------------------------------------------------

@app.function(image=image, timeout=180)
@modal.fastapi_endpoint(method="POST", label="score")
def score_endpoint(payload: dict) -> dict:
    """POST /score with JSON body { content_b64: str, filename?: str }.

    Returns the cohort-by-cohort ranking + percentile.

    CORS is permissive (anyone can call from the Vercel domain). For a school
    project this is fine; tighten if you ever care.
    """
    if not isinstance(payload, dict):
        return {"ok": False, "error": "expected JSON object"}

    b64 = payload.get("content_b64")
    text = payload.get("text")
    filename = payload.get("filename")

    if b64:
        try:
            body = base64.b64decode(b64)
        except Exception as e:
            return {"ok": False, "error": f"invalid base64: {e}"}
    elif text and isinstance(text, str):
        body = text.encode("utf-8")
    else:
        return {"ok": False, "error": "supply content_b64 or text"}

    if len(body) > MAX_FILE_BYTES:
        return {"ok": False, "error": f"file too large (>{MAX_FILE_BYTES} bytes)"}

    return Inference().score.remote(body=body, filename=filename)


@app.function()
@modal.fastapi_endpoint(method="GET", label="health")
def health() -> dict:
    return {"ok": True, "cohorts": COHORTS}
