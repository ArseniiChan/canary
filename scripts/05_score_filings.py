"""Phase 4 — score every filing under its cohort's autoencoder.

For each cohort C:
  * Load the cohort's autoencoder (data/processed/models/<ticker>.pt)
  * Score the fraud filing AND every clean peer filing
  * Emit one row per filing to data/results/scores.csv

Also persists per-sentence error arrays (used by Phase 5 Mann-Whitney) to
data/processed/per_sentence/<ticker>__<accession>.npy
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.autoencoder import MODEL_DIR, load_cohort_autoencoder
from engine.edgar import _strip_dashes
from engine.embeddings import EmbeddingEngine, _cache_path
from engine.scoring import score_filing


def _load_emb(accession: str) -> np.ndarray:
    p = _cache_path(accession, EmbeddingEngine().model_name)
    if not p.exists():
        return np.zeros((0, 384), dtype=np.float32)
    data = np.load(p, allow_pickle=True)
    return data["embeddings"].astype(np.float32)


def main() -> int:
    fraud_manifest = json.loads((REPO_ROOT / "data/processed/fraud_manifest.json").read_text())
    cohorts = json.loads((REPO_ROOT / "data/processed/cohorts.json").read_text())
    parsed = json.loads((REPO_ROOT / "data/processed/parsed_index.json").read_text())
    parsed_by_acc = {r["accession"]: r for r in parsed["filings"] if r["success"]}

    fraud_by_ticker = {f["ticker"]: f for f in fraud_manifest["frauds"] if f["status"] == "OK"}

    out_csv = REPO_ROOT / "data/results/scores.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    per_sent_dir = REPO_ROOT / "data/processed/per_sentence"
    per_sent_dir.mkdir(parents=True, exist_ok=True)

    with out_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "filing_id", "accession", "fraud_or_peer", "cohort_id",
            "cik", "filing_date", "report_date",
            "n_sentences", "score_mean", "score_trimmed_mean", "score_max",
        ])

        for c in cohorts["cohorts"]:
            ticker = c["fraud_ticker"]
            model_path = MODEL_DIR / f"{ticker}.pt"
            if not model_path.exists():
                print(f"[{ticker}] no model at {model_path}; skipping")
                continue
            model = load_cohort_autoencoder(model_path)

            # Fraud filing
            fraud = fraud_by_ticker.get(ticker)
            if fraud is None:
                print(f"[{ticker}] no fraud entry in manifest; skipping")
                continue
            fraud_emb = _load_emb(fraud["accession"])
            if fraud_emb.size == 0:
                print(f"[{ticker}] fraud embeddings missing for {fraud['accession']}")
                continue
            sf = score_filing(fraud["accession"], fraud_emb, model)
            np.save(
                per_sent_dir / f"{ticker}__{_strip_dashes(fraud['accession'])}.npy",
                sf.per_sentence,
            )
            w.writerow([
                f"{ticker}_fraud", fraud["accession"], "fraud", ticker,
                fraud["cik"], fraud["filing_date"], fraud["report_date"],
                sf.n_sentences, f"{sf.mean_recon_error:.6f}",
                f"{sf.trimmed_mean_recon_error:.6f}", f"{sf.max_recon_error:.6f}",
            ])

            # Clean peers
            peer_count = 0
            for p in c["peers"]:
                if not p["is_clean"]:
                    continue
                if p["accession"] not in parsed_by_acc:
                    continue
                emb = _load_emb(p["accession"])
                if emb.size == 0:
                    continue
                sp = score_filing(p["accession"], emb, model)
                np.save(
                    per_sent_dir / f"{ticker}__{_strip_dashes(p['accession'])}.npy",
                    sp.per_sentence,
                )
                w.writerow([
                    f"{ticker}_peer_{p['cik']}", p["accession"], "peer", ticker,
                    p["cik"], p["filing_date"], p["report_date"],
                    sp.n_sentences, f"{sp.mean_recon_error:.6f}",
                    f"{sp.trimmed_mean_recon_error:.6f}", f"{sp.max_recon_error:.6f}",
                ])
                peer_count += 1
            print(f"[{ticker}] scored fraud + {peer_count} peers")

    print(f"\nWrote {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
