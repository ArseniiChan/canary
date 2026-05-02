"""Phase 1 — assemble industry- and year-matched peer cohorts for each fraud.

For each fraud target loaded from ``data/processed/fraud_manifest.json``:

  1. Build a candidate cohort (SIC-2 + same calendar year of period-of-report,
     fraud's own CIK excluded).
  2. Apply the operational clean rule from ``engine/clean_screening``.
  3. Target 6 - 12 clean peers per cohort. If fewer than 6 clean peers, mark
     the cohort as a SIC-1 fallback and re-run candidate construction at the
     SIC-1 level.
  4. Download each peer's primary 10-K document into the EDGAR cache.
  5. Emit two artifacts:
       - ``data/processed/cohorts.json``  (machine-readable, used by later phases)
       - ``reports/cohort_overview.md``   (human-readable, for the appendix)

Idempotent: every step uses the EDGAR on-disk cache, so reruns only do work
that is missing.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.clean_screening import _load_denylist, screen_peer
from engine.edgar import EdgarClient, FilingRef
from engine.sic_matching import build_candidate_cohort, get_company_sic

TARGET_MIN = 6
TARGET_MAX = 12
DENYLIST_DIR = REPO_ROOT / "data" / "processed"


@dataclass
class CohortPeer:
    cik: str
    name: str
    sic: str
    sic_description: str
    accession: str
    filing_date: str
    report_date: str
    primary_document: str
    primary_doc_url: str
    is_clean: bool
    flags: list[str]
    notes: list[str]
    distance: int = 0  # 0=same SIC4, 1=same SIC2, 2=same SIC1 fallback

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class Cohort:
    fraud_name: str
    fraud_ticker: str
    fraud_cik: str
    fraud_accession: str
    fraud_filing_date: str
    fraud_period: str
    fraud_sic: str
    fraud_sic2: str
    period_year: int
    peers: list[CohortPeer] = field(default_factory=list)
    used_sic1_fallback: bool = False
    notes: list[str] = field(default_factory=list)

    def clean_peers(self) -> list[CohortPeer]:
        return [p for p in self.peers if p.is_clean]


def _resolve_candidates(
    client: EdgarClient,
    sic2: str,
    period_year: int,
    fraud_cik: str,
    fraud_sic: str,
) -> list[FilingRef]:
    return build_candidate_cohort(
        client,
        sic2,
        period_year,
        exclude_ciks=[fraud_cik],
        progress=True,
    )


def _annotate_and_screen(
    client: EdgarClient,
    candidates: list[FilingRef],
    fraud_sic: str,
    *,
    aaer_dl: tuple[set[str], set[str]],
    ca_dl: tuple[set[str], set[str]],
    distance_floor: int = 0,
) -> list[CohortPeer]:
    out: list[CohortPeer] = []
    fraud_sic2 = fraud_sic[:2] if fraud_sic else ""
    for ref in candidates:
        sic, sic_desc, name = get_company_sic(client, ref.cik)
        screen = screen_peer(
            client,
            ref.cik,
            name,
            ref.filing_date,
            aaer_denylist=aaer_dl,
            classaction_denylist=ca_dl,
        )
        # distance: 0 if SIC4 == fraud_sic, 1 if SIC2 prefix matches, 2 otherwise (SIC-1 fallback territory)
        if sic and fraud_sic and sic == fraud_sic:
            d = 0
        elif sic and fraud_sic2 and sic.startswith(fraud_sic2):
            d = 1
        else:
            d = max(2, distance_floor)
        out.append(
            CohortPeer(
                cik=ref.cik,
                name=name,
                sic=sic,
                sic_description=sic_desc,
                accession=ref.accession,
                filing_date=ref.filing_date,
                report_date=ref.report_date,
                primary_document=ref.primary_document,
                primary_doc_url=ref.primary_doc_url,
                is_clean=screen.is_clean,
                flags=list(screen.flags),
                notes=list(screen.notes),
                distance=max(d, distance_floor),
            )
        )
    return out


def _build_cohort_for_fraud(
    client: EdgarClient,
    fraud: dict,
    aaer_dl: tuple[set[str], set[str]],
    ca_dl: tuple[set[str], set[str]],
) -> Cohort:
    fraud_sic = fraud["sic"] or ""
    fraud_sic2 = fraud_sic[:2] if fraud_sic else ""
    fraud_sic1 = fraud_sic[:1] if fraud_sic else ""
    period_year = int(str(fraud["report_date"])[:4]) if fraud["report_date"] else fraud["fiscal_year"]
    cohort = Cohort(
        fraud_name=fraud["name"],
        fraud_ticker=fraud["ticker"],
        fraud_cik=fraud["cik"],
        fraud_accession=fraud["accession"],
        fraud_filing_date=fraud["filing_date"],
        fraud_period=fraud["report_date"],
        fraud_sic=fraud_sic,
        fraud_sic2=fraud_sic2,
        period_year=period_year,
    )
    if not fraud_sic2:
        cohort.notes.append("No SIC reported by EDGAR — cohort not buildable.")
        return cohort

    print(f"\n=== {fraud['name']}  CIK={fraud['cik']}  SIC={fraud_sic}  period_year={period_year} ===")
    print(f"[1/3] candidate cohort by SIC-2={fraud_sic2}, period_year={period_year} ...")
    candidates = _resolve_candidates(
        client, fraud_sic2, period_year, fraud["cik"], fraud_sic
    )
    print(f"      candidates found: {len(candidates)}")

    print(f"[2/3] applying clean rule ...")
    annotated = _annotate_and_screen(
        client, candidates, fraud_sic, aaer_dl=aaer_dl, ca_dl=ca_dl
    )
    n_clean = sum(1 for p in annotated if p.is_clean)
    print(f"      clean candidates: {n_clean} of {len(annotated)}")

    if n_clean < TARGET_MIN and fraud_sic1:
        print(f"      FALLBACK: SIC-2 cohort below target_min={TARGET_MIN}; expanding to SIC-1={fraud_sic1}")
        cohort.used_sic1_fallback = True
        # Iterate every SIC-2 starting with fraud_sic1, skipping the one we already did
        extra_candidates: list[FilingRef] = []
        for sic2_candidate in (f"{fraud_sic1}{d}" for d in "0123456789"):
            if sic2_candidate == fraud_sic2:
                continue
            extra = build_candidate_cohort(
                client, sic2_candidate, period_year,
                exclude_ciks=[fraud["cik"]] + [p.cik for p in annotated],
                progress=False,
            )
            extra_candidates.extend(extra)
        extra_annotated = _annotate_and_screen(
            client, extra_candidates, fraud_sic, aaer_dl=aaer_dl, ca_dl=ca_dl, distance_floor=2,
        )
        annotated.extend(extra_annotated)
        n_clean = sum(1 for p in annotated if p.is_clean)
        cohort.notes.append(
            f"SIC-2 cohort yielded only {n_clean - sum(1 for p in extra_annotated if p.is_clean)} clean peers; "
            f"expanded to SIC-1={fraud_sic1} (fallback flagged)."
        )

    # Sort: clean first; within clean, lower distance first; within distance, by SIC similarity to fraud.
    annotated.sort(key=lambda p: (
        not p.is_clean,
        p.distance,
        0 if p.sic == fraud_sic else 1,
        p.cik,
    ))

    # Truncate to TARGET_MAX clean peers (keep all dirty ones in record but only TARGET_MAX clean)
    clean_kept = []
    dirty_kept = []
    for p in annotated:
        if p.is_clean and len(clean_kept) < TARGET_MAX:
            clean_kept.append(p)
        elif not p.is_clean:
            dirty_kept.append(p)
    cohort.peers = clean_kept + dirty_kept

    # Download primary docs for the peers we'll actually use (clean ones)
    print(f"[3/3] downloading primary 10-Ks for {len(clean_kept)} clean peers ...")
    for p in clean_kept:
        ref = FilingRef(
            cik=p.cik,
            accession=p.accession,
            form="10-K",
            filing_date=p.filing_date,
            report_date=p.report_date,
            primary_document=p.primary_document,
        )
        try:
            client.fetch_filing_document(ref)
        except Exception as e:
            p.flags.append("download_failed")
            p.notes.append(f"download error: {e}")
    return cohort


def _emit_cohort_overview_md(cohorts: list[Cohort], path: Path) -> None:
    lines: list[str] = []
    lines.append("# Cohort Overview")
    lines.append("")
    lines.append(
        "Generated by `scripts/01_pull_filings.py`. Per-fraud peer lists with "
        "SIC, accession, filing date, and clean-rule outcome. SIC-1 fallback is "
        "flagged separately; flagged cohorts are excluded from primary results "
        "per the analysis spec."
    )
    lines.append("")
    for c in cohorts:
        clean = c.clean_peers()
        lines.append(f"## {c.fraud_name} (`{c.fraud_ticker}`)")
        lines.append("")
        lines.append(
            f"- Fraud CIK: `{c.fraud_cik}` · SIC: `{c.fraud_sic}` "
            f"({c.fraud_period[:4] if c.fraud_period else '?'}) · "
            f"period year matched: {c.period_year}"
        )
        lines.append(
            f"- Clean peers: **{len(clean)}** "
            f"({'**SIC-1 fallback**' if c.used_sic1_fallback else 'SIC-2 only'})"
        )
        if c.notes:
            for n in c.notes:
                lines.append(f"- Note: {n}")
        lines.append("")
        lines.append("| # | Clean? | CIK | Company | SIC | Accession | Filed | Period | Flags |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for i, p in enumerate(c.peers, 1):
            ok = "OK" if p.is_clean else "—"
            flags = ", ".join(p.flags) if p.flags else ""
            lines.append(
                f"| {i} | {ok} | {p.cik} | {p.name[:48]} | {p.sic} | "
                f"`{p.accession}` | {p.filing_date} | {p.report_date} | {flags} |"
            )
        lines.append("")
    path.write_text("\n".join(lines) + "\n")
    print(f"Wrote {path}")


def main() -> int:
    print("=" * 72)
    print("Phase 1 — assembling SIC-matched clean peer cohorts")
    print("=" * 72)

    manifest_path = REPO_ROOT / "data" / "processed" / "fraud_manifest.json"
    if not manifest_path.exists():
        print(f"FAIL: {manifest_path} missing — run scripts/00_pin_accessions.py first.")
        return 1
    manifest = json.loads(manifest_path.read_text())
    frauds = [f for f in manifest["frauds"] if f["status"] == "OK"]

    client = EdgarClient()
    aaer_dl = _load_denylist(DENYLIST_DIR / "aaer_denylist.txt")
    ca_dl = _load_denylist(DENYLIST_DIR / "classaction_denylist.txt")

    cohorts: list[Cohort] = []
    for f in frauds:
        cohorts.append(_build_cohort_for_fraud(client, f, aaer_dl, ca_dl))

    out_json = REPO_ROOT / "data" / "processed" / "cohorts.json"
    out_md = REPO_ROOT / "reports" / "cohort_overview.md"
    out_md.parent.mkdir(parents=True, exist_ok=True)

    payload = {"cohorts": [
        {
            "fraud_name": c.fraud_name,
            "fraud_ticker": c.fraud_ticker,
            "fraud_cik": c.fraud_cik,
            "fraud_accession": c.fraud_accession,
            "fraud_filing_date": c.fraud_filing_date,
            "fraud_period": c.fraud_period,
            "fraud_sic": c.fraud_sic,
            "fraud_sic2": c.fraud_sic2,
            "period_year": c.period_year,
            "used_sic1_fallback": c.used_sic1_fallback,
            "notes": c.notes,
            "peers": [p.to_dict() for p in c.peers],
            "n_clean_peers": len(c.clean_peers()),
        }
        for c in cohorts
    ]}
    out_json.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"\nWrote {out_json}")

    _emit_cohort_overview_md(cohorts, out_md)

    print("\n" + "=" * 72)
    print("Phase 1 cohort summary:")
    print("=" * 72)
    failures = []
    for c in cohorts:
        n = len(c.clean_peers())
        flag = "FALLBACK" if c.used_sic1_fallback else "ok"
        marker = "OK" if n >= TARGET_MIN else "SHORT"
        print(f"  [{marker}] {c.fraud_ticker:<6} clean_peers={n:>3}  ({flag})")
        if n < TARGET_MIN:
            failures.append((c.fraud_ticker, n))

    if failures:
        print(f"\nWARN: {len(failures)} cohort(s) below target_min={TARGET_MIN}: {failures}")
        print("Review reports/cohort_overview.md and consider expanding deny-lists or accepting smaller cohort.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
