"""Sanity-check cohort assembly for Enron's exact SIC4=6200 only (not full SIC2)."""

from __future__ import annotations

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.edgar import EdgarClient
from engine.sic_matching import companies_with_sic_prefix, find_peer_10k_for_year

t0 = time.monotonic()
client = EdgarClient()
print("Enumerating SIC=6200 companies...")
companies = companies_with_sic_prefix(client, "6200", max_pages=20)
print(f"  found {len(companies)} CIKs in {time.monotonic()-t0:.1f}s")

if companies:
    print(f"  first few: {[c.name[:50] for c in companies[:5]]}")

print("\nLooking for 10-Ks with period in calendar year 2000 (Enron's fiscal year)...")
matches = []
for i, c in enumerate(companies):
    ref = find_peer_10k_for_year(client, c.cik, 2000)
    if ref is not None:
        matches.append((c, ref))
    if (i + 1) % 25 == 0:
        print(f"  ...processed {i+1}/{len(companies)}, matches so far: {len(matches)}")

print(f"\n{len(matches)} matches in calendar 2000 from SIC=6200")
for c, ref in matches[:10]:
    print(f"  CIK={c.cik}  {c.name[:50]:<50}  acc={ref.accession}  filed={ref.filing_date}  period={ref.report_date}")

print(f"\nTotal time: {time.monotonic()-t0:.1f}s")
