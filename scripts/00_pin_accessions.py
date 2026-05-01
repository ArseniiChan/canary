"""Phase 0.4 — verify and pin EDGAR accession numbers for the six fraud 10-Ks.

For each entry in FRAUD_TARGETS:
  1. Fetch submissions JSON from EDGAR
  2. Find the 10-K whose period-of-report ends in the specified fiscal year
  3. Verify that filing_date strictly pre-dates the documented public-revelation date
  4. Download the primary document so it lives in the cache (deterministic for later phases)
  5. Append a row to analysis_spec.md and a machine-readable JSON manifest

After this script runs cleanly, the user (NOT this script) commits analysis_spec.md
and applies the immutable git tag `validation-spec-frozen` BEFORE Phase 5 validation runs.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.edgar import EdgarClient, FilingRef


@dataclass
class FraudTarget:
    name: str
    ticker: str  # informal — for figures and dashboard slugs
    cik: str
    fiscal_year: int
    revelation_date: str  # ISO; the filing_date must be strictly less than this
    revelation_event: str
    revelation_source: str


FRAUD_TARGETS: list[FraudTarget] = [
    FraudTarget(
        name="Enron Corp.",
        ticker="ENE",
        cik="0001024401",
        fiscal_year=2000,
        revelation_date="2001-10-16",
        revelation_event="Q3 earnings release: $618M loss, $1.2B equity write-down",
        revelation_source="SEC complaint; press archive (Wall Street Journal, Houston Chronicle, Oct 17 2001)",
    ),
    FraudTarget(
        name="WorldCom Inc.",
        ticker="WCOM",
        cik="0000723527",
        fiscal_year=2001,
        revelation_date="2002-06-25",
        revelation_event="Announcement of $3.8B accounting fraud (line-cost capitalization)",
        revelation_source="SEC AAER 1568 / SEC press release Jun 26 2002",
    ),
    FraudTarget(
        name="Tyco International Ltd.",
        ticker="TYC",
        cik="0000833444",
        fiscal_year=2001,
        revelation_date="2002-06-03",
        revelation_event="Indictment of CEO L. Dennis Kozlowski (NY DA)",
        revelation_source="NY District Attorney filings; SEC litigation release LR-17722",
    ),
    FraudTarget(
        name="HealthSouth Corp.",
        ticker="HRC",
        cik="0000785161",
        fiscal_year=2001,
        revelation_date="2003-03-19",
        revelation_event="SEC civil complaint alleging $2.7B fraud",
        revelation_source="SEC litigation release LR-18044",
    ),
    FraudTarget(
        name="Valeant Pharmaceuticals International Inc.",
        ticker="VRX",
        cik="0000885590",
        fiscal_year=2014,
        revelation_date="2015-10-19",
        revelation_event="Citron Research short report alleging Philidor channel stuffing",
        revelation_source="Citron Research published report Oct 21 2015 (initial allegations Oct 19 in social media); subsequent SEC investigation",
    ),
    FraudTarget(
        name="Lehman Brothers Holdings Inc.",
        ticker="LEH",
        cik="0000806085",
        fiscal_year=2007,
        revelation_date="2008-09-15",
        revelation_event="Chapter 11 bankruptcy filing (Repo 105 disclosed in Mar 2010 examiner's report)",
        revelation_source="Bankruptcy court docket; Valukas examiner's report (Mar 2010)",
    ),
]


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_one(client: EdgarClient, t: FraudTarget) -> dict:
    print(f"\n--- {t.name} (CIK {t.cik}, FY{t.fiscal_year}) ---")
    sub = client.submissions(t.cik)
    sic = sub.get("sic") or ""
    sic_desc = sub.get("sicDescription") or ""
    entity_name = sub.get("name") or sub.get("entityName") or t.name
    print(f"  EDGAR entity: {entity_name}")
    print(f"  SIC: {sic} ({sic_desc})")

    filing: FilingRef | None = client.find_10k_for_fiscal_year(t.cik, t.fiscal_year)
    status = "OK"
    error = None
    sha256 = None
    size = None

    if filing is None:
        status = "FAIL"
        error = f"No 10-K found with reportDate in {t.fiscal_year}"
        print(f"  FAIL: {error}")
        return {
            "name": t.name,
            "ticker": t.ticker,
            "cik": t.cik,
            "fiscal_year": t.fiscal_year,
            "edgar_entity_name": entity_name,
            "sic": sic,
            "sic_description": sic_desc,
            "accession": None,
            "filing_date": None,
            "report_date": None,
            "primary_document": None,
            "primary_doc_url": None,
            "primary_doc_sha256": None,
            "primary_doc_size_bytes": None,
            "revelation_date": t.revelation_date,
            "revelation_event": t.revelation_event,
            "revelation_source": t.revelation_source,
            "pre_discovery_verified": False,
            "status": status,
            "error": error,
        }

    print(f"  accession  : {filing.accession}")
    print(f"  filed      : {filing.filing_date}")
    print(f"  period     : {filing.report_date}")
    print(f"  primary    : {filing.primary_document}")
    print(f"  url        : {filing.primary_doc_url}")

    pre_discovery = filing.filing_date < t.revelation_date
    if not pre_discovery:
        status = "FAIL"
        error = (
            f"Filing date {filing.filing_date} is NOT strictly less than "
            f"revelation date {t.revelation_date}"
        )
        print(f"  FAIL: {error}")
    else:
        days = (
            datetime.fromisoformat(t.revelation_date) - datetime.fromisoformat(filing.filing_date)
        ).days
        print(f"  pre-discovery: OK  ({days} days before public revelation)")

    if status == "OK":
        path = client.fetch_filing_document(filing)
        size = path.stat().st_size
        sha256 = _sha256_of_file(path)
        print(f"  cached     : {path}  ({size:,} bytes)")
        print(f"  sha256     : {sha256}")
        if size < 50_000:
            print(f"  WARN: primary document unusually small ({size} bytes) — verify manually")

    return {
        "name": t.name,
        "ticker": t.ticker,
        "cik": t.cik,
        "fiscal_year": t.fiscal_year,
        "edgar_entity_name": entity_name,
        "sic": sic,
        "sic_description": sic_desc,
        "accession": filing.accession,
        "filing_date": filing.filing_date,
        "report_date": filing.report_date,
        "primary_document": filing.primary_document,
        "primary_doc_url": filing.primary_doc_url,
        "primary_doc_sha256": sha256,
        "primary_doc_size_bytes": size,
        "revelation_date": t.revelation_date,
        "revelation_event": t.revelation_event,
        "revelation_source": t.revelation_source,
        "pre_discovery_verified": pre_discovery,
        "status": status,
        "error": error,
    }


def _emit_spec_markdown(rows: list[dict], path: Path) -> None:
    """Emit the human-readable analysis_spec.md."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines: list[str] = []
    lines.append("# Canary — Frozen Analysis Specification")
    lines.append("")
    lines.append("**Status:** This file is the frozen analysis spec. It is committed to git ")
    lines.append("and tagged `validation-spec-frozen` BEFORE Phase 5 validation runs. Single-pass ")
    lines.append("results from `scripts/06_validate.py` are reported as-is.")
    lines.append("")
    lines.append(f"**Generated:** {today}")
    lines.append("")
    lines.append("## 1. Held-out fraud evaluation set (six 10-K filings, all pre-discovery)")
    lines.append("")
    lines.append(
        "| # | Company | CIK | FY | Accession | Filed | Period | Pre-discovery | SIC | SIC desc |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        flag = "OK" if r["pre_discovery_verified"] else "**FAIL**"
        acc = r["accession"] or "—"
        filed = r["filing_date"] or "—"
        period = r["report_date"] or "—"
        lines.append(
            f"| {i} | {r['name']} | {r['cik']} | {r['fiscal_year']} | "
            f"`{acc}` | {filed} | {period} | {flag} | "
            f"{r['sic']} | {r['sic_description']} |"
        )
    lines.append("")
    lines.append("### Per-target verification detail")
    lines.append("")
    for r in rows:
        lines.append(f"#### {r['name']} (`{r['ticker']}`)")
        lines.append("")
        lines.append(f"- EDGAR entity name: `{r['edgar_entity_name']}`")
        lines.append(f"- CIK: `{r['cik']}`  ·  SIC: `{r['sic']}` ({r['sic_description']})")
        lines.append(f"- Fiscal year: **{r['fiscal_year']}**")
        if r["accession"]:
            lines.append(f"- Accession (frozen): `{r['accession']}`")
            lines.append(f"- Filing date: **{r['filing_date']}**")
            lines.append(f"- Period of report: {r['report_date']}")
            lines.append(f"- Primary document: `{r['primary_document']}`")
            lines.append(f"- Primary doc URL: <{r['primary_doc_url']}>")
            lines.append(f"- Primary doc size: {r['primary_doc_size_bytes']:,} bytes")
            lines.append(f"- Primary doc SHA-256: `{r['primary_doc_sha256']}`")
        else:
            lines.append("- Accession: **NOT FOUND**")
        lines.append(f"- Public revelation date: **{r['revelation_date']}**")
        lines.append(f"- Revelation event: {r['revelation_event']}")
        lines.append(f"- Source for revelation date: {r['revelation_source']}")
        if r["pre_discovery_verified"]:
            from datetime import datetime as _dt
            days = (
                _dt.fromisoformat(r["revelation_date"]) - _dt.fromisoformat(r["filing_date"])  # type: ignore[arg-type]
            ).days
            lines.append(f"- **Verified pre-discovery:** {days} days between filing and revelation.")
        elif r["status"] == "FAIL":
            lines.append(f"- **VERIFICATION FAIL:** {r['error']}")
        lines.append("")

    lines.append("## 2. Frozen primary configuration")
    lines.append("")
    lines.append("```")
    lines.append("embedding model       : sentence-transformers/all-MiniLM-L6-v2  (dim=384)")
    lines.append("autoencoder           : 384 -> 128 -> 32 -> 128 -> 384, ReLU, MSE, Adam(lr=1e-3)")
    lines.append("training              : 200 epochs, batch 16, 20% validation split, early stopping")
    lines.append("seeds                 : numpy=42, torch=42, python=42")
    lines.append("sentence cap          : 100 per filing during training (uniform sample if more)")
    lines.append("filing-level score    : mean per-sentence reconstruction error")
    lines.append("statistical test      : Mann-Whitney U on fraud vs peer sentence-level errors")
    lines.append("bootstrap             : 1,000 filing-level resamples within cohort")
    lines.append("null permutation      : 1,000 within-cohort label shuffles")
    lines.append("training regime       : leave-one-cohort-out + time-controlled (filings <= fraud filing date)")
    lines.append("peer matching         : SIC-2-digit + same fiscal year; SIC-1 fallback if SIC-2 < 6")
    lines.append("clean-peer rule       : no AAER + no Item 4.02 / 10-K/A within 5 yrs + no class-action settlement > $1M within 5 yrs")
    lines.append("primary aggregation   : mean (ablations: trimmed-mean@5%, max — appendix only)")
    lines.append("primary sentence cap  : 100 (ablations: 50, 200 — appendix only)")
    lines.append("entity-masking ablation: Enron only, appendix")
    lines.append("```")
    lines.append("")
    lines.append("## 3. Reporting metrics (per fraud + aggregate)")
    lines.append("")
    lines.append("- Cohort size, exact rank within cohort, percentile rank")
    lines.append("- Hit@1, Hit@3, Hit@5 paired with random-baseline expected value")
    lines.append("- Mann-Whitney U statistic, p-value, effect size (rank-biserial)")
    lines.append("- Bootstrap 95% CI on rank (1,000 filing-level resamples)")
    lines.append("- Null-permutation empirical p-value of `rank <= k` (1,000 permutations)")
    lines.append("- Leave-one-fraud-out aggregate sensitivity (Section 6 of report)")
    lines.append("")
    lines.append("## 4. Phase 1 cohorts (filled in by `scripts/01_pull_filings.py`)")
    lines.append("")
    lines.append(
        "Per-fraud SIC-2 cohort lists (CIK + accession + filing date) appended after Phase 1, "
        "documenting any SIC-1 fallbacks separately. Fallback cohorts are excluded from primary "
        "results and reported separately."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**Once this file is committed and tagged `validation-spec-frozen`, ")
    lines.append("no further edits to the analysis configuration are made before validation. ")
    lines.append("Whatever the numbers say, that's the result.**")
    path.write_text("\n".join(lines) + "\n")
    print(f"\nWrote spec markdown -> {path}")


def _emit_manifest_json(rows: list[dict], path: Path) -> None:
    payload = {
        "generated_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "frauds": rows,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote machine-readable manifest -> {path}")


def main() -> int:
    print("=" * 72)
    print("Phase 0.4 — pinning EDGAR accession numbers for 6 fraud 10-Ks")
    print("=" * 72)
    client = EdgarClient()
    print(f"User-Agent: {client.user_agent}\n")

    rows = [_verify_one(client, t) for t in FRAUD_TARGETS]

    spec_md = REPO_ROOT / "analysis_spec.md"
    manifest_dir = REPO_ROOT / "data" / "processed"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_json = manifest_dir / "fraud_manifest.json"

    _emit_spec_markdown(rows, spec_md)
    _emit_manifest_json(rows, manifest_json)

    print("\n" + "=" * 72)
    n_ok = sum(1 for r in rows if r["status"] == "OK")
    n_fail = len(rows) - n_ok
    print(f"Verified pre-discovery: {n_ok}/{len(rows)}  ·  Failures: {n_fail}")
    print("=" * 72)
    if n_fail:
        for r in rows:
            if r["status"] != "OK":
                print(f"  - {r['name']}: {r['error']}")
        return 3

    print(
        "\nNEXT (manual): commit analysis_spec.md and tag `validation-spec-frozen` "
        "BEFORE running Phase 5 validation."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
