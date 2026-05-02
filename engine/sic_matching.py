"""SIC-based peer cohort enumeration.

EDGAR does not expose a single API that filters filings by both SIC and
period-of-report year. We work around this in two stages:

  1. ``companies_with_sic_prefix(prefix)`` enumerates every CIK whose current
     SIC code begins with the given prefix (typically a 2-digit SIC). It uses
     the legacy ``browse-edgar?action=getcompany&SIC=XXXX`` HTML interface
     which is the only EDGAR endpoint that filters companies by SIC. Results
     are cached on disk.

  2. ``find_peer_10k_for_year(cik, fiscal_year)`` reuses :class:`EdgarClient`
     to pull the company's submissions JSON (cached) and find a 10-K (or
     10-K405) whose period-of-report falls in the target calendar year.

Combining the two gives us a full SIC-2 + report-year peer list. The current
SIC for each company comes from EDGAR's submissions JSON ("sic" field) — we
intentionally use whatever EDGAR currently reports rather than reconstructing
historical SIC codes, because (a) EDGAR's historical SIC is not exposed as a
field, (b) the alternative — manual reclassification — would inject an
analyst-controlled variable into peer matching, and (c) the same convention is
applied symmetrically to the fraud filings themselves (see analysis_spec.md).
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup

from engine.edgar import EdgarClient, FilingRef, _pad_cik

BROWSE_EDGAR_HOST = "www.sec.gov"
BROWSE_EDGAR_BASE = "https://www.sec.gov/cgi-bin/browse-edgar"
PAGE_SIZE = 100  # browse-edgar caps `count` at 100


@dataclass
class CompanyRecord:
    cik: str  # 10-digit padded
    name: str
    sic: str  # 4-digit current SIC


def _parse_company_listing(html: str) -> list[CompanyRecord]:
    """Parse a browse-edgar `action=getcompany` HTML page into CIK + name records."""
    soup = BeautifulSoup(html, "lxml")
    out: list[CompanyRecord] = []
    # The result table has class 'tableFile2' on modern EDGAR pages
    table = soup.find("table", class_="tableFile2") or soup.find("table", summary=re.compile("^Results"))
    if table is None:
        # Sometimes EDGAR returns the simpler companies index — try generic table
        for tbl in soup.find_all("table"):
            if tbl.find("a", href=re.compile(r"CIK=\d+")):
                table = tbl
                break
    if table is None:
        return out

    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue
        cik_link = tr.find("a", href=re.compile(r"CIK=\d+"))
        if cik_link is None:
            continue
        m = re.search(r"CIK=(\d+)", cik_link["href"])
        if not m:
            continue
        cik = _pad_cik(m.group(1))
        # company name: the cell content of the first td that doesn't hold the CIK link
        name = tds[1].get_text(strip=True) if len(tds) >= 2 else cik_link.get_text(strip=True)
        # SIC code: appears in the URL params or a separate cell — leave blank if unknown
        out.append(CompanyRecord(cik=cik, name=name, sic=""))
    return out


def companies_with_sic_prefix(
    client: EdgarClient,
    sic_prefix: str,
    *,
    max_pages: int = 200,
) -> list[CompanyRecord]:
    """Enumerate every CIK whose current SIC starts with ``sic_prefix``.

    SIC codes on EDGAR are 4-digit. Browse-edgar matches the SIC field exactly,
    so a 2-digit prefix like "62" needs to expand into all 100 possible 4-digit
    SICs starting with "62" -- but that would multiply requests for no gain.
    Instead we leverage the fact that browse-edgar's `SIC=XXXX` *also* accepts
    a wildcard-suffix when fewer than 4 digits are supplied (it filters by
    leading match). We send the raw prefix.

    We also walk multi-page results via the `start` offset and de-duplicate.
    """
    seen: dict[str, CompanyRecord] = {}
    for page in range(max_pages):
        offset = page * PAGE_SIZE
        url = (
            f"{BROWSE_EDGAR_BASE}?action=getcompany&SIC={sic_prefix}"
            f"&type=10-K&dateb=&owner=include&count={PAGE_SIZE}&start={offset}"
        )
        body = client.fetch_url(url, host=BROWSE_EDGAR_HOST)
        records = _parse_company_listing(body.decode("utf-8", errors="replace"))
        if not records:
            break
        new_count = 0
        for r in records:
            if r.cik not in seen:
                seen[r.cik] = r
                new_count += 1
        # Some SEC responses repeat the last page when offset > total. Stop if no new records.
        if new_count == 0:
            break
    return list(seen.values())


def companies_with_sic2(
    client: EdgarClient,
    sic2: str,
) -> list[CompanyRecord]:
    """Enumerate all CIKs whose current SIC starts with the given 2-digit prefix.

    Implemented by issuing one browse-edgar query per 4-digit SIC in the prefix
    range, which is more reliable than relying on browse-edgar's
    leading-match behaviour (which is undocumented).
    """
    if not (sic2.isdigit() and len(sic2) == 2):
        raise ValueError(f"sic2 must be a 2-digit numeric string, got {sic2!r}")
    aggregate: dict[str, CompanyRecord] = {}
    for digit_pair in range(100):
        sic4 = f"{sic2}{digit_pair:02d}"
        records = companies_with_sic_prefix(client, sic4, max_pages=20)
        for r in records:
            r.sic = sic4
            aggregate.setdefault(r.cik, r)
    return list(aggregate.values())


def find_peer_10k_for_year(
    client: EdgarClient,
    cik: str | int,
    period_year: int,
) -> FilingRef | None:
    """Find a 10-K filing for the given CIK whose period-of-report ends in ``period_year``.

    Returns ``None`` if the company has no 10-K (or 10-K405) for that calendar year.
    Uses the existing ``find_10k_for_fiscal_year`` helper which already handles
    pre-2003 form variants.
    """
    try:
        return client.find_10k_for_fiscal_year(cik, period_year)
    except Exception:
        # 404 or transient error — caller treats as "no filing found"
        return None


def get_company_sic(client: EdgarClient, cik: str | int) -> tuple[str, str, str]:
    """Return ``(sic, sic_description, current_name)`` from cached submissions JSON."""
    sub = client.submissions(cik)
    return (
        str(sub.get("sic") or ""),
        str(sub.get("sicDescription") or ""),
        str(sub.get("name") or sub.get("entityName") or ""),
    )


def build_candidate_cohort(
    client: EdgarClient,
    sic2: str,
    period_year: int,
    *,
    exclude_ciks: Iterable[str] = (),
    progress: bool = True,
) -> list[FilingRef]:
    """Build a candidate peer cohort: every CIK with SIC-2 ``sic2`` that filed a
    10-K (or 10-K405) with period-of-report ending in calendar year ``period_year``.

    The returned list excludes any CIK in ``exclude_ciks`` (typically the
    fraud's own CIK). It is the *candidate* list — clean-screening
    (Item 4.02 / 10-K/A / class action / AAER) happens in
    :mod:`engine.clean_screening`.
    """
    excluded = {_pad_cik(c) for c in exclude_ciks}
    companies = companies_with_sic2(client, sic2)

    out: list[FilingRef] = []
    iterator = companies
    if progress:
        try:
            from tqdm import tqdm

            iterator = tqdm(
                companies,
                desc=f"SIC{sic2} → 10-K[{period_year}]",
                unit="cik",
            )
        except ImportError:
            iterator = companies

    for c in iterator:
        if c.cik in excluded:
            continue
        ref = find_peer_10k_for_year(client, c.cik, period_year)
        if ref is not None:
            out.append(ref)
    return out
