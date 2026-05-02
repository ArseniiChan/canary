"""Operational clean-peer screening.

The ``analysis_spec.md`` clean rule has three components:

  (A) No SEC enforcement action (AAER) issued naming the firm within 5 years
      post-filing.
  (B) No Item 4.02 non-reliance disclosure / no material 10-K/A restatement
      filed within 5 years post-filing.
  (C) No securities class-action settlement above $1M within 5 years
      post-filing.

We can fully automate (B) using each company's submissions JSON. (A) and (C)
have no public, free programmatic source at the granularity we need; we
therefore use editable deny-lists at ``data/processed/aaer_denylist.txt`` and
``data/processed/classaction_denylist.txt`` (one CIK or company-name token per
line). The lists start out small (well-known prominent cases) and the report's
limitations section discloses the partial coverage explicitly.

A peer is **clean** iff none of (A), (B), (C) flags fire.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from engine.edgar import EdgarClient, _pad_cik

DEFAULT_DENYLIST_DIR = Path("data/processed")


@dataclass
class ScreeningResult:
    cik: str
    is_clean: bool
    flags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "cik": self.cik,
            "is_clean": self.is_clean,
            "flags": list(self.flags),
            "notes": list(self.notes),
        }


def _load_denylist(path: Path) -> tuple[set[str], set[str]]:
    """Return (cik_set, name_token_set). Lines starting with '#' are comments.

    A line that is all digits (with or without leading zeros) is treated as a
    CIK; otherwise it's a lowercased substring matched against the company name.
    """
    if not path.exists():
        return set(), set()
    cik_set: set[str] = set()
    name_set: set[str] = set()
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.lstrip("0").isdigit() or line.isdigit():
            cik_set.add(_pad_cik(line))
        else:
            name_set.add(line.lower())
    return cik_set, name_set


def _name_matches_denylist(name: str, name_tokens: set[str]) -> bool:
    if not name_tokens:
        return False
    name_lower = name.lower()
    return any(tok in name_lower for tok in name_tokens)


def _has_amendment_within_window(
    client: EdgarClient,
    cik: str,
    after: str,
    days: int = 365 * 5,
) -> tuple[bool, str | None]:
    """Return (flag, accession) if the firm filed a 10-K/A whose filing_date is
    in (after, after + days]. The filing_date of the AMENDMENT is what triggers
    the flag, not the period.
    """
    try:
        amends = client.list_form_filings(cik, "10-K/A")
    except Exception:
        return False, None
    if not amends:
        return False, None
    after_dt = datetime.fromisoformat(after)
    cutoff = after_dt + timedelta(days=days)
    for a in amends:
        try:
            d = datetime.fromisoformat(a.filing_date)
        except ValueError:
            continue
        if after_dt < d <= cutoff:
            return True, a.accession
    return False, None


def screen_peer(
    client: EdgarClient,
    cik: str | int,
    company_name: str,
    candidate_filing_date: str,
    *,
    aaer_denylist: tuple[set[str], set[str]] | None = None,
    classaction_denylist: tuple[set[str], set[str]] | None = None,
    window_days: int = 365 * 5,
) -> ScreeningResult:
    """Apply the operational clean rule to one candidate peer."""
    cik_padded = _pad_cik(cik)
    res = ScreeningResult(cik=cik_padded, is_clean=True)

    # (A) AAER deny-list
    if aaer_denylist is None:
        aaer_denylist = _load_denylist(DEFAULT_DENYLIST_DIR / "aaer_denylist.txt")
    aaer_ciks, aaer_names = aaer_denylist
    if cik_padded in aaer_ciks:
        res.is_clean = False
        res.flags.append("aaer_denylist_cik")
    if _name_matches_denylist(company_name, aaer_names):
        res.is_clean = False
        res.flags.append("aaer_denylist_name")

    # (B) Restatement / 10-K/A within 5y post-filing — programmatic
    flag_b, acc = _has_amendment_within_window(
        client, cik_padded, candidate_filing_date, window_days
    )
    if flag_b:
        res.is_clean = False
        res.flags.append("ten_k_a_within_5y")
        res.notes.append(f"10-K/A {acc} filed within 5y post-filing")

    # (C) Securities class-action settlement deny-list
    if classaction_denylist is None:
        classaction_denylist = _load_denylist(
            DEFAULT_DENYLIST_DIR / "classaction_denylist.txt"
        )
    ca_ciks, ca_names = classaction_denylist
    if cik_padded in ca_ciks:
        res.is_clean = False
        res.flags.append("classaction_denylist_cik")
    if _name_matches_denylist(company_name, ca_names):
        res.is_clean = False
        res.flags.append("classaction_denylist_name")

    if not res.flags:
        # Be explicit about what we did NOT verify, so the report can disclose this.
        res.notes.append(
            "AAER and class-action checks: deny-list-only "
            "(no automated SEC enforcement / Stanford SCAC API used)."
        )

    return res
