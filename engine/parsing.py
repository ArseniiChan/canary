"""MD&A (Item 7) extraction from 10-K filings.

10-K filings on EDGAR come in two main formats in our cohort:

  * Old plain-text / SGML (pre-2002 era — Enron, WorldCom, Tyco, HealthSouth):
    a single ``.txt`` file with an SGML wrapper. Item headers are typically
    in ALL CAPS without HTML markup.
  * Modern HTML (Valeant 2014, Lehman 2007 era): an ``.htm`` file with the
    section structured via tables and tags.

We use a unified extractor that:

  1. Strips HTML to plain text if needed (BeautifulSoup with a permissive parser).
  2. Locates the **Item 7** header that introduces the MD&A section. Several
     candidate regexes are tried in priority order; the LAST occurrence in the
     document is preferred over the first because the first hit is almost
     always a Table of Contents entry.
  3. Locates the **end-of-MD&A** boundary, which is typically Item 7A
     (Quantitative & Qualitative Disclosures About Market Risk) or, when 7A
     is absent or missed, Item 8 (Financial Statements).
  4. Extracts the slice between, cleans whitespace, and returns the body text
     plus a small extraction-status record for the QA pipeline.

The extraction is deliberately conservative: we'd rather report a parse failure
and fall through to the manual-fix queue than silently emit a mis-bounded MD&A
that would leak into embeddings.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup

# Note: ALL pattern strings are deliberately tolerant of:
#   * "Item 7", "ITEM 7", "Item 7.", "ITEM 7.", "Item Seven"
#   * non-breaking spaces, multiple whitespace, leading newlines
#   * occasional HTML noise (we strip HTML first when applicable)
ITEM7_HEAD = re.compile(
    r"(?:^|\n|>)\s*"
    r"(?:item\s*7\b|ITEM\s*7\b|Item\s+Seven\b|ITEM\s+SEVEN\b)"
    r"(?!\s*[Aa])"  # not Item 7A
    r"[\.\s]*"
    r"(?:management['’]?s\s+discussion|management\s+s\s+discussion|MANAGEMENT['’]?S\s+DISCUSSION)?",
    re.IGNORECASE,
)

ITEM7A_HEAD = re.compile(
    r"(?:^|\n|>)\s*"
    r"(?:item\s*7\s*a\b|ITEM\s*7\s*A\b|item\s*7\.\s*a\b)"
    r"[\.\s]*"
    r"(?:quantitative\s+and\s+qualitative|QUANTITATIVE\s+AND\s+QUALITATIVE)?",
    re.IGNORECASE,
)

ITEM8_HEAD = re.compile(
    r"(?:^|\n|>)\s*"
    r"(?:item\s*8\b|ITEM\s*8\b|Item\s+Eight\b)"
    r"[\.\s]*"
    r"(?:financial\s+statements|FINANCIAL\s+STATEMENTS|consolidated|CONSOLIDATED)?",
    re.IGNORECASE,
)

ITEM6_HEAD = re.compile(
    r"(?:^|\n|>)\s*(?:item\s*6\b|ITEM\s*6\b)",
    re.IGNORECASE,
)

# Sentence splitter: simple, pragmatic, avoids NLTK as a dependency.
# Splits on `. ` / `! ` / `? ` followed by uppercase or digit; preserves common
# abbreviations like "U.S." and "Inc." by NOT splitting if the preceding token
# matches a small abbreviations list.
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\(\"“])")
_ABBREV = {
    "U.S.", "Inc.", "Corp.", "Co.", "Ltd.", "Mr.", "Mrs.", "Dr.", "St.",
    "No.", "Jr.", "Sr.", "vs.", "Fig.", "e.g.", "i.e.", "etc.", "Est.",
    "Sec.", "Ms.",
}


@dataclass
class ExtractionResult:
    accession: str
    primary_document: str
    success: bool
    method: str  # which strategy succeeded ("html_item7_to_7a", "txt_item7_to_8", etc.)
    text: str
    char_count: int
    sentence_count: int
    notes: list[str]
    error: str | None = None

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        # Don't ship the entire MD&A body in the QA report
        d["text_preview"] = (self.text[:300] + "…") if self.text else ""
        d.pop("text", None)
        return d


def _strip_html(text: str) -> str:
    """If text looks like HTML, render to text via BeautifulSoup; otherwise return as-is."""
    sample = text[:500].lower()
    looks_html = ("<html" in sample or "<body" in sample or "<div" in sample
                  or "<table" in sample or "<p>" in sample or "<font" in sample)
    if not looks_html:
        return text
    soup = BeautifulSoup(text, "lxml")
    # Drop script/style noise
    for tag in soup(["script", "style"]):
        tag.decompose()
    rendered = soup.get_text("\n")
    return rendered


def _normalize_whitespace(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\xa0", " ")
    # Collapse runs of blank lines
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    return s.strip()


def _all_matches(pattern: re.Pattern[str], text: str) -> list[re.Match[str]]:
    return list(pattern.finditer(text))


# Anchor for fallback when "Item 7" is not visible at the real MD&A start
# (older incorporation-by-reference style filings like Tyco 2001).
MDNA_HEADER = re.compile(
    r"MANAGEMENT['’]?S\s+DISCUSSION\s+AND\s+ANALYSIS"
    r"(?:\s+OF\s+FINANCIAL\s+CONDITION)?",
    re.IGNORECASE,
)
QUANT_HEADER = re.compile(
    r"QUANTITATIVE\s+AND\s+QUALITATIVE\s+DISCLOSURES?",
    re.IGNORECASE,
)
FINSTAT_HEADER = re.compile(
    r"(?:REPORT\s+OF\s+INDEPENDENT|INDEPENDENT\s+AUDITORS?\s+REPORT|"
    r"FINANCIAL\s+STATEMENTS\s+AND\s+SUPPLEMENTARY\s+DATA)",
    re.IGNORECASE,
)

MIN_BODY_CHARS = 3_000
MAX_BODY_CHARS = 400_000
IDEAL_MIN = 8_000
IDEAL_MAX = 230_000


def _toc_threshold(text_len: int) -> int:
    """Position past which we trust an Item 7 hit to be a real body header."""
    return max(5_000, int(text_len * 0.04))


def _candidate_end_boundaries(text: str) -> list[tuple[int, str]]:
    """All candidate end-of-MD&A positions, descending priority."""
    out: list[tuple[int, str]] = []
    for label, pat in [
        ("last_item7a", ITEM7A_HEAD),
        ("last_item8", ITEM8_HEAD),
        ("last_quantitative_anchor", QUANT_HEADER),
        ("last_finstmt_anchor", FINSTAT_HEADER),
    ]:
        hits = _all_matches(pat, text)
        if hits:
            out.append((hits[-1].start(), label))
    # Deduplicate by position (latest label wins)
    seen: set[int] = set()
    deduped: list[tuple[int, str]] = []
    for pos, lbl in out:
        if pos in seen:
            continue
        seen.add(pos)
        deduped.append((pos, lbl))
    return deduped


def _candidate_start_positions(text: str, end_pos: int) -> list[tuple[int, str]]:
    """All candidate MD&A start positions before ``end_pos``, descending priority.

    A candidate Item 7 hit is treated as a TOC entry (not a real body header)
    when it is followed within 1000 chars by an Item 7A or Item 8 header. Such
    pairs appear together on cover pages and TOC entries; the real MD&A body
    has thousands of chars between Item 7 and Item 7A/8.
    """
    threshold = _toc_threshold(len(text))
    out: list[tuple[int, str]] = []

    # Real Item 7 starts: first hit past TOC threshold AND not immediately
    # followed by Item 7A/8 (which would mark it as a TOC entry).
    item7s = [m for m in _all_matches(ITEM7_HEAD, text)
              if threshold <= m.start() < end_pos]
    item7a_starts = [m.start() for m in _all_matches(ITEM7A_HEAD, text)]
    item8_starts = [m.start() for m in _all_matches(ITEM8_HEAD, text)]

    def is_toc_pair(item7_pos: int) -> bool:
        for p in item7a_starts:
            if 0 < p - item7_pos < 1000:
                return True
        for p in item8_starts:
            if 0 < p - item7_pos < 1000:
                return True
        return False

    real_item7s = [m for m in item7s if not is_toc_pair(m.start())]
    if real_item7s:
        out.append((real_item7s[0].end(), "first_item7_after_toc"))

    mdna_anchors = [m for m in _all_matches(MDNA_HEADER, text)
                    if threshold <= m.start() < end_pos]
    if mdna_anchors:
        out.append((mdna_anchors[-1].start(), "last_mdna_anchor"))
        out.append((mdna_anchors[0].start(), "first_mdna_anchor_after_toc"))
    return out


def split_sentences(text: str) -> list[str]:
    """Conservative regex-based sentence splitter."""
    if not text:
        return []
    # Soft-protect abbreviations: replace dots in known abbrevs with a sentinel.
    sentinel = "\x00"
    protected = text
    for ab in _ABBREV:
        protected = protected.replace(ab, ab.replace(".", sentinel))
    parts = _SENTENCE_END.split(protected)
    out: list[str] = []
    for p in parts:
        s = p.replace(sentinel, ".").strip()
        # Drop trivial fragments
        if len(s) < 20:
            continue
        # Drop sentences that are mostly digits / table fallout
        digits = sum(c.isdigit() for c in s)
        if digits > len(s) * 0.5:
            continue
        out.append(s)
    return out


def extract_mdna(raw_bytes: bytes, accession: str, primary_document: str) -> ExtractionResult:
    """Extract the MD&A (Item 7) body from a 10-K filing's primary document bytes."""
    notes: list[str] = []

    try:
        text = raw_bytes.decode("utf-8", errors="replace")
    except Exception as e:  # pragma: no cover — decode is forgiving
        return ExtractionResult(
            accession=accession,
            primary_document=primary_document,
            success=False,
            method="decode_failed",
            text="",
            char_count=0,
            sentence_count=0,
            notes=notes,
            error=str(e),
        )

    text = _strip_html(text)
    text = _normalize_whitespace(text)

    ends = _candidate_end_boundaries(text)
    if not ends:
        return ExtractionResult(
            accession=accession,
            primary_document=primary_document,
            success=False,
            method="no_end_boundary",
            text="",
            char_count=0,
            sentence_count=0,
            notes=notes,
            error="Could not locate Item 7A / Item 8 / financial-statements anchor",
        )

    # Try (start, end) candidate pairs in priority order. Accept the first
    # pair that produces a body in the ideal range. If none does, accept the
    # first that produces a body in the broader [MIN, MAX] range.
    best_body = ""
    best_method = ""
    last_error = "no candidate pair produced a usable body"
    for end_pos, end_method in ends:
        for start_pos, start_method in _candidate_start_positions(text, end_pos):
            if start_pos >= end_pos:
                continue
            cand = text[start_pos:end_pos].strip()
            cand = _normalize_whitespace(cand)
            if IDEAL_MIN <= len(cand) <= IDEAL_MAX:
                best_body = cand
                best_method = f"{start_method}__{end_method}"
                last_error = ""
                break
            if MIN_BODY_CHARS <= len(cand) <= MAX_BODY_CHARS and not best_body:
                best_body = cand
                best_method = f"{start_method}__{end_method}__outside_ideal"
                last_error = (
                    f"Body {len(cand)} chars accepted but outside ideal "
                    f"range [{IDEAL_MIN}, {IDEAL_MAX}]"
                )
        if best_method and "__outside_ideal" not in best_method:
            break

    if not best_body or len(best_body) < MIN_BODY_CHARS:
        return ExtractionResult(
            accession=accession,
            primary_document=primary_document,
            success=False,
            method=best_method or "no_anchor_pair",
            text=best_body,
            char_count=len(best_body),
            sentence_count=0,
            notes=notes,
            error=last_error,
        )
    if not (IDEAL_MIN <= len(best_body) <= IDEAL_MAX):
        notes.append(
            f"WARN: body length {len(best_body)} chars is outside ideal "
            f"range [{IDEAL_MIN:,}, {IDEAL_MAX:,}] — review for boundary errors"
        )

    start_method, end_method = best_method.split("__", 1)
    body = best_body
    if len(body) > MAX_BODY_CHARS:
        notes.append(f"WARN: body is {len(body)} chars — possibly over-large boundary")
    start_pos = 0  # for parity with old method-name composition
    sentences = split_sentences(body)
    if len(sentences) < 20:
        notes.append(
            f"WARN: only {len(sentences)} sentences extracted — possible parse boundary error"
        )

    return ExtractionResult(
        accession=accession,
        primary_document=primary_document,
        success=True,
        method=best_method,
        text=body,
        char_count=len(body),
        sentence_count=len(sentences),
        notes=notes,
        error=None,
    )


def extract_mdna_from_path(path: str | Path, accession: str = "") -> ExtractionResult:
    p = Path(path)
    if not accession:
        accession = p.parent.name
    return extract_mdna(p.read_bytes(), accession=accession, primary_document=p.name)
