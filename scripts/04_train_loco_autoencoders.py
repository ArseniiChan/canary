"""Phase 3 — train one autoencoder per fraud cohort under LOCO + time-controlled inputs.

For each fraud cohort C:
  * training set = clean peer filings from cohorts OTHER THAN C, AND with
    filing_date <= C's fraud filing_date
  * model = engine.autoencoder.CanaryAutoencoder
  * artifacts saved to data/processed/models/<ticker>.pt
  * training results appended to data/processed/training_log.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.autoencoder import MODEL_DIR, train_cohort_autoencoder
from engine.edgar import _strip_dashes
from engine.embeddings import EmbeddingEngine, _cache_path  # _cache_path is deliberately reused


def _load_embeddings(accession: str) -> np.ndarray:
    p = _cache_path(accession, EmbeddingEngine().model_name)
    if not p.exists():
        return np.zeros((0, 384), dtype=np.float32)
    data = np.load(p, allow_pickle=True)
    return data["embeddings"].astype(np.float32)


def main() -> int:
    fraud_path = REPO_ROOT / "data/processed/fraud_manifest.json"
    cohort_path = REPO_ROOT / "data/processed/cohorts.json"
    parsed_idx = REPO_ROOT / "data/processed/parsed_index.json"
    for p in (fraud_path, cohort_path, parsed_idx):
        if not p.exists():
            print(f"FAIL: {p} missing — earlier phase has not completed.")
            return 1

    fraud_manifest = json.loads(fraud_path.read_text())
    cohorts = json.loads(cohort_path.read_text())
    parsed = json.loads(parsed_idx.read_text())

    parsed_by_acc = {r["accession"]: r for r in parsed["filings"] if r["success"]}

    # Build a peer index keyed by ticker -> list[(accession, filing_date)] for clean peers
    peers_by_ticker: dict[str, list[tuple[str, str]]] = {}
    for c in cohorts["cohorts"]:
        ticker = c["fraud_ticker"]
        keep = []
        for p in c["peers"]:
            if not p["is_clean"]:
                continue
            if p["accession"] not in parsed_by_acc:
                continue
            keep.append((p["accession"], p["filing_date"]))
        peers_by_ticker[ticker] = keep

    fraud_filing_date_by_ticker = {
        f["ticker"]: f["filing_date"]
        for f in fraud_manifest["frauds"]
        if f["status"] == "OK"
    }

    log: list[dict] = []
    for c in cohorts["cohorts"]:
        ticker = c["fraud_ticker"]
        cutoff = fraud_filing_date_by_ticker[ticker]
        # LOCO: take peers from EVERY cohort EXCEPT this one
        train_filings: list[tuple[str, np.ndarray]] = []
        for other_ticker, peers in peers_by_ticker.items():
            if other_ticker == ticker:
                continue
            for acc, fdate in peers:
                # Time-controlled: only include peers dated <= the fraud's filing_date
                if fdate > cutoff:
                    continue
                emb = _load_embeddings(acc)
                if emb.size == 0:
                    continue
                train_filings.append((acc, emb))
        if not train_filings:
            print(f"[{ticker}] NO training data after LOCO + time filter — skipping")
            continue
        print(f"[{ticker}] training on {len(train_filings)} peer filings (LOCO + cutoff <= {cutoff})")
        result = train_cohort_autoencoder(
            ticker, train_filings, out_dir=MODEL_DIR,
        )
        log.append(result.__dict__)
        print(
            f"  -> n_sent={result.n_train_sentences:>5}  "
            f"best_val={result.best_val_loss:.5f} @ epoch {result.best_epoch}  "
            f"epochs_run={result.n_epochs_run}"
        )

    log_path = REPO_ROOT / "data/processed/training_log.json"
    log_path.write_text(json.dumps({"runs": log}, indent=2) + "\n")
    print(f"\nWrote {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
