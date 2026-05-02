"""Phase 3 — compute MiniLM sentence embeddings for every parsed filing.

Reads:
  data/processed/parsed_index.json  (output of scripts/02_parse_filings.py)
  data/processed/parsed/<accession_nodash>.txt

Writes:
  data/processed/embeddings/<accession_nodash>__<model_hash>.npz

Idempotent: skips filings whose embeddings cache already exists with the
same sentence list.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.edgar import _strip_dashes
from engine.embeddings import EmbeddingEngine
from engine.parsing import split_sentences


def main() -> int:
    idx_path = REPO_ROOT / "data/processed/parsed_index.json"
    if not idx_path.exists():
        print(f"FAIL: {idx_path} missing — run scripts/02_parse_filings.py first.")
        return 1
    idx = json.loads(idx_path.read_text())

    parsed_dir = REPO_ROOT / "data/processed/parsed"
    targets: list[tuple[str, list[str]]] = []
    for r in idx["filings"]:
        if not r["success"]:
            continue
        body_path = parsed_dir / f"{_strip_dashes(r['accession'])}.txt"
        if not body_path.exists():
            print(f"  WARN: missing parsed body for {r['accession']} at {body_path}")
            continue
        body = body_path.read_text(encoding="utf-8")
        sentences = split_sentences(body)
        if not sentences:
            print(f"  WARN: zero sentences for {r['accession']}")
            continue
        targets.append((r["accession"], sentences))

    print(f"Encoding {len(targets)} filings with MiniLM ...")
    engine = EmbeddingEngine()
    for i, (acc, sents) in enumerate(targets, 1):
        emb = engine.encode_filing(acc, sents)
        if i % 5 == 0 or i == len(targets):
            print(f"  [{i:>3}/{len(targets)}] {acc}  n_sent={emb.n_sentences}")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
