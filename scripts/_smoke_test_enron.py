"""Phase 0 smoke test — pull Enron FY2000 10-K end-to-end.

Hard gate: if this fails, do NOT proceed to Phase 0.4 (accession pinning).
Run from the repo root:

    .venv/bin/python scripts/_smoke_test_enron.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.edgar import EdgarClient

ENRON_CIK = "0001024401"
ENRON_FY = 2000
PUBLIC_REVELATION_DATE = "2001-10-16"  # Q3 earnings release


def main() -> int:
    print("=" * 72)
    print("Phase 0 smoke test — Enron FY2000 10-K")
    print("=" * 72)

    client = EdgarClient()
    print(f"User-Agent: {client.user_agent}")

    print("\n[1/4] Fetching Enron submissions JSON ...")
    sub = client.submissions(ENRON_CIK)
    name = sub.get("name") or sub.get("entityName") or "<unknown>"
    sic = sub.get("sic") or "<unknown>"
    sic_desc = sub.get("sicDescription") or "<unknown>"
    print(f"      entity: {name}")
    print(f"      SIC: {sic} ({sic_desc})")

    print("\n[2/4] Listing all 10-K filings ...")
    tenks = client.list_form_filings(ENRON_CIK, "10-K")
    print(f"      found {len(tenks)} 10-K filings")
    for f in tenks:
        print(f"        - filing_date={f.filing_date}  report_date={f.report_date}  acc={f.accession}")

    print(f"\n[3/4] Locating 10-K for FY{ENRON_FY} ...")
    filing = client.find_10k_for_fiscal_year(ENRON_CIK, ENRON_FY)
    if filing is None:
        print(f"      FAIL: no 10-K with reportDate in {ENRON_FY}")
        return 1
    print(f"      accession        : {filing.accession}")
    print(f"      filing_date      : {filing.filing_date}")
    print(f"      report_date      : {filing.report_date}")
    print(f"      primary_document : {filing.primary_document}")
    print(f"      url              : {filing.primary_doc_url}")
    print(f"      revelation_date  : {PUBLIC_REVELATION_DATE}")

    if filing.filing_date >= PUBLIC_REVELATION_DATE:
        print(f"      FAIL: filing_date {filing.filing_date} is NOT before public revelation")
        return 2

    print(f"      OK: filing pre-dates public revelation ({filing.filing_date} < {PUBLIC_REVELATION_DATE})")

    print("\n[4/4] Downloading primary 10-K document ...")
    path = client.fetch_filing_document(filing).resolve()
    size = path.stat().st_size
    try:
        rel = path.relative_to(REPO_ROOT)
    except ValueError:
        rel = path
    print(f"      saved to {rel}  ({size:,} bytes)")

    if size < 50_000:
        print(f"      WARN: document is unusually small ({size} bytes)")

    head = path.read_bytes()[:512].decode("utf-8", errors="replace")
    has_html = "<html" in head.lower() or "<HTML" in head
    has_text = "ENRON" in head.upper() or "10-K" in head.upper() or "ANNUAL REPORT" in head.upper()
    print(f"      HTML-ish: {has_html}  ENRON/10-K mentioned in header: {has_text}")

    print("\n" + "=" * 72)
    print("Smoke test PASSED. Phase 0.3 gate cleared.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
