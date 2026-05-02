"""Smoke test the MD&A extractor against Enron's 2000 10-K."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.parsing import extract_mdna_from_path

ENRON_PATH = REPO_ROOT / "data/raw/edgar/filings/000102440101500010/ene10-k.txt"
res = extract_mdna_from_path(ENRON_PATH, accession="0001024401-01-500010")
print(f"success     : {res.success}")
print(f"method      : {res.method}")
print(f"char_count  : {res.char_count:,}")
print(f"sentences   : {res.sentence_count}")
print(f"notes       : {res.notes}")
print(f"error       : {res.error}")
print()
print("--- first 800 chars ---")
print(res.text[:800])
print("...")
print("--- last 400 chars ---")
print(res.text[-400:])
