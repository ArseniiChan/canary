"""Phase 2 — extract MD&A (Item 7) from every fraud + peer filing in the cohorts.

Inputs:
  data/processed/fraud_manifest.json
  data/processed/cohorts.json

For each filing referenced in those manifests:
  1. Read the cached primary document from data/raw/edgar/filings/<accession_nodash>/
  2. Run engine.parsing.extract_mdna
  3. Write the extracted body to data/processed/parsed/<accession_nodash>.txt (UTF-8)
  4. Append a row to data/processed/parsed_index.json with extraction metadata

Output:
  data/processed/parsed/                 — one .txt file per successfully parsed filing
  data/processed/parsed_index.json       — machine-readable extraction status for every filing
  reports/parsing_qa.md                  — human-readable extraction QA report

HARD GATE per analysis spec: extraction success rate must be >= 80%. The script
exits non-zero if below the gate; that signals to the operator that the parser
needs improvement before proceeding to Phase 3 (embeddings).

Manual extraction fixes (if any) are logged in reports/parsing_qa.md so they
can be applied symmetrically to fraud and peer filings, and reviewed.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.edgar import _strip_dashes
from engine.parsing import extract_mdna_from_path

EXTRACTION_GATE = 0.80


def _filing_path(accession: str, primary_document: str) -> Path:
    return REPO_ROOT / "data/raw/edgar/filings" / _strip_dashes(accession) / primary_document


def _parsed_path(accession: str) -> Path:
    return REPO_ROOT / "data/processed/parsed" / f"{_strip_dashes(accession)}.txt"


def _gather_targets() -> list[dict]:
    """Build the unified list of filings to parse.

    Each row carries: kind ('fraud'|'peer'), cohort_id, ticker, cik, accession,
    filing_date, period, primary_document.
    """
    fraud_path = REPO_ROOT / "data/processed/fraud_manifest.json"
    cohort_path = REPO_ROOT / "data/processed/cohorts.json"
    if not fraud_path.exists():
        raise FileNotFoundError(f"missing {fraud_path} — run scripts/00_pin_accessions.py first")
    if not cohort_path.exists():
        raise FileNotFoundError(f"missing {cohort_path} — run scripts/01_pull_filings.py first")

    fraud_manifest = json.loads(fraud_path.read_text())
    cohorts = json.loads(cohort_path.read_text())

    rows: list[dict] = []
    fraud_by_ticker: dict[str, dict] = {}
    for f in fraud_manifest["frauds"]:
        if f["status"] != "OK":
            continue
        fraud_by_ticker[f["ticker"]] = f
        rows.append({
            "kind": "fraud",
            "cohort_id": f["ticker"],
            "ticker": f["ticker"],
            "cik": f["cik"],
            "accession": f["accession"],
            "filing_date": f["filing_date"],
            "report_date": f["report_date"],
            "primary_document": f["primary_document"],
            "period_year": int(str(f["report_date"])[:4]) if f["report_date"] else f["fiscal_year"],
        })

    for c in cohorts["cohorts"]:
        ticker = c["fraud_ticker"]
        for p in c["peers"]:
            # Only parse clean peers — dirty ones are recorded for the appendix
            # but never enter the autoencoder pipeline.
            if not p["is_clean"]:
                continue
            rows.append({
                "kind": "peer",
                "cohort_id": ticker,
                "ticker": ticker,
                "cik": p["cik"],
                "accession": p["accession"],
                "filing_date": p["filing_date"],
                "report_date": p["report_date"],
                "primary_document": p["primary_document"],
                "period_year": int(str(p["report_date"])[:4]) if p["report_date"] else c["period_year"],
            })
    return rows


def _emit_qa_md(rows: list[dict], out_path: Path) -> None:
    success = sum(1 for r in rows if r["success"])
    total = len(rows)
    rate = success / total if total else 0.0

    by_kind: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_kind[r["kind"]].append(r)
    by_year: dict[int, list[dict]] = defaultdict(list)
    for r in rows:
        by_year[r["period_year"]].append(r)
    by_cohort: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_cohort[r["cohort_id"]].append(r)

    lines: list[str] = []
    lines.append("# Parsing QA")
    lines.append("")
    lines.append(
        f"**Overall:** {success}/{total} filings successfully parsed "
        f"(**{rate:.1%}** success). Hard gate: >= {EXTRACTION_GATE:.0%}."
    )
    lines.append("")
    lines.append("## Success rate by fraud/peer status")
    lines.append("")
    lines.append("| Kind | Successful | Total | Rate |")
    lines.append("|---|---|---|---|")
    for kind in ("fraud", "peer"):
        rs = by_kind.get(kind, [])
        if not rs:
            continue
        s = sum(1 for r in rs if r["success"])
        lines.append(f"| {kind} | {s} | {len(rs)} | {s/len(rs):.1%} |")
    lines.append("")

    lines.append("## Success rate by period year")
    lines.append("")
    lines.append("| Year | Successful | Total | Rate |")
    lines.append("|---|---|---|---|")
    for year in sorted(by_year.keys()):
        rs = by_year[year]
        s = sum(1 for r in rs if r["success"])
        lines.append(f"| {year} | {s} | {len(rs)} | {s/len(rs):.1%} |")
    lines.append("")

    lines.append("## Per-cohort detail")
    lines.append("")
    for ticker in sorted(by_cohort.keys()):
        rs = by_cohort[ticker]
        s = sum(1 for r in rs if r["success"])
        lines.append(f"### {ticker} cohort")
        lines.append("")
        lines.append(f"- {s}/{len(rs)} parsed successfully ({s/len(rs):.1%})")
        lines.append("")
        lines.append("| Kind | CIK | Accession | Method | Chars | Sentences | Error |")
        lines.append("|---|---|---|---|---|---|---|")
        for r in rs:
            err = (r.get("error") or "")[:80]
            lines.append(
                f"| {r['kind']} | {r['cik']} | `{r['accession']}` | "
                f"{r['method']} | {r['char_count']:,} | {r['sentence_count']} | {err} |"
            )
        lines.append("")

    lines.append("## Failures (for manual review)")
    lines.append("")
    fails = [r for r in rows if not r["success"]]
    if not fails:
        lines.append("_None._")
    else:
        for r in fails:
            lines.append(
                f"- `{r['accession']}`  ({r['ticker']}/{r['kind']})  "
                f"method={r['method']}  chars={r['char_count']}  error={r['error']}"
            )
    lines.append("")
    out_path.write_text("\n".join(lines) + "\n")
    print(f"Wrote QA report -> {out_path}")


def main() -> int:
    print("=" * 72)
    print("Phase 2 — extracting MD&A from every cohort filing")
    print("=" * 72)

    targets = _gather_targets()
    print(f"Targets: {len(targets)} filings ({sum(1 for t in targets if t['kind']=='fraud')} fraud, {sum(1 for t in targets if t['kind']=='peer')} peer)")

    out_dir = REPO_ROOT / "data/processed/parsed"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for t in targets:
        path = _filing_path(t["accession"], t["primary_document"])
        if not path.exists():
            rows.append({
                **t,
                "success": False,
                "method": "missing_primary_document",
                "char_count": 0,
                "sentence_count": 0,
                "error": f"raw filing not found at {path.relative_to(REPO_ROOT)}",
                "notes": [],
                "parsed_path": None,
            })
            continue
        res = extract_mdna_from_path(path, accession=t["accession"])
        parsed_rel: str | None = None
        if res.success:
            parsed_path = _parsed_path(t["accession"])
            parsed_path.write_text(res.text, encoding="utf-8")
            parsed_rel = str(parsed_path.relative_to(REPO_ROOT))
        rows.append({
            **t,
            "success": res.success,
            "method": res.method,
            "char_count": res.char_count,
            "sentence_count": res.sentence_count,
            "error": res.error,
            "notes": res.notes,
            "parsed_path": parsed_rel,
        })

    # Write machine-readable index
    idx_path = REPO_ROOT / "data/processed/parsed_index.json"
    idx_path.write_text(json.dumps({"filings": rows}, indent=2) + "\n")
    print(f"\nWrote {idx_path}")

    qa_path = REPO_ROOT / "reports/parsing_qa.md"
    qa_path.parent.mkdir(parents=True, exist_ok=True)
    _emit_qa_md(rows, qa_path)

    n_ok = sum(1 for r in rows if r["success"])
    n_total = len(rows)
    rate = n_ok / n_total if n_total else 0.0
    print("\n" + "=" * 72)
    print(f"Parse success: {n_ok}/{n_total} = {rate:.1%}  (gate: {EXTRACTION_GATE:.0%})")
    print("=" * 72)
    if rate < EXTRACTION_GATE:
        print(
            "FAIL: extraction success below gate. Inspect reports/parsing_qa.md and "
            "improve engine/parsing.py before proceeding to Phase 3."
        )
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
