"""Tests for engine/parsing.py — MD&A extraction."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.parsing import (
    extract_mdna,
    extract_mdna_from_path,
    split_sentences,
    _normalize_whitespace,
    _strip_html,
    _toc_threshold,
)


def test_normalize_whitespace_collapses_blank_lines():
    s = "first line\n\n\n\nsecond line\n\n\nthird"
    assert _normalize_whitespace(s) == "first line\n\nsecond line\n\nthird"


def test_normalize_whitespace_drops_nbsp():
    s = "alpha\xa0beta\xa0gamma"
    assert _normalize_whitespace(s) == "alpha beta gamma"


def test_strip_html_passes_through_plain_text():
    s = "ITEM 7. MANAGEMENT'S DISCUSSION\nThe company had a good year."
    assert _strip_html(s) == s


def test_strip_html_renders_html_to_text():
    s = "<html><body><p>Hello <b>world</b></p></body></html>"
    out = _strip_html(s)
    assert "Hello" in out and "world" in out
    assert "<b>" not in out


def test_split_sentences_drops_short_fragments():
    s = "This is a long enough first sentence. Yes! This second one is also long enough to keep."
    sents = split_sentences(s)
    assert len(sents) == 2
    assert all(len(sent) >= 20 for sent in sents)


def test_split_sentences_protects_common_abbreviations():
    s = (
        "The company is incorporated in the U.S. and has multiple subsidiaries."
        " Mr. Smith is the CEO. Inc. and Corp. abbreviations should not split sentences."
    )
    sents = split_sentences(s)
    assert any("U.S." in s for s in sents)


def _synthetic_filing(mdna_paragraphs: int = 30) -> bytes:
    """Build a synthetic 10-K with a recognizable MD&A section."""
    paras = [
        f"In fiscal {2000+i}, the Company recognized substantial revenue from "
        f"continuing operations and managed working capital prudently. Liquidity "
        f"remained adequate to meet short-term obligations and the company "
        f"continued to invest in research and development."
        for i in range(mdna_paragraphs)
    ]
    body = "\n\n".join(paras)
    doc = (
        "FORM 10-K\n\nTABLE OF CONTENTS\n"
        "Item 1. Business\n"
        "Item 7. Management's Discussion and Analysis\n"
        "Item 7A. Quantitative and Qualitative Disclosures\n"
        "Item 8. Financial Statements\n"
        "\n" + ("X" * 6000) + "\n"
        "ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION\n\n"
        + body + "\n\n"
        "ITEM 7A. QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK\n\n"
        "Market risk is monitored by the treasury function.\n"
    )
    return doc.encode("utf-8")


def test_extract_mdna_finds_synthetic_section():
    raw = _synthetic_filing()
    res = extract_mdna(raw, accession="ACC-1", primary_document="10k.txt")
    assert res.success is True
    assert res.char_count > 5000
    assert "Liquidity" in res.text
    assert res.sentence_count > 5


def test_extract_mdna_rejects_too_short_body():
    body = (
        "FORM 10-K\nTABLE OF CONTENTS\n"
        + ("X" * 6000)
        + "\nITEM 7. MANAGEMENT'S DISCUSSION\nVery short.\n"
        + "ITEM 7A. QUANTITATIVE AND QUALITATIVE\n"
    )
    res = extract_mdna(body.encode("utf-8"), accession="ACC-2", primary_document="10k.txt")
    assert res.success is False
    assert "short" in (res.error or "").lower() or "no candidate" in (res.error or "").lower()


def test_toc_threshold_scales_with_doc_size():
    assert _toc_threshold(10_000) >= 5_000
    assert _toc_threshold(1_000_000) >= 40_000


@pytest.mark.skipif(
    not (REPO_ROOT / "data/raw/edgar/filings/000102440101500010/ene10-k.txt").exists(),
    reason="Enron 10-K not in cache",
)
def test_extract_mdna_real_enron_filing():
    """Integration test against the real Enron 10-K (in cache after Phase 0)."""
    p = REPO_ROOT / "data/raw/edgar/filings/000102440101500010/ene10-k.txt"
    res = extract_mdna_from_path(p, accession="0001024401-01-500010")
    assert res.success is True
    assert res.char_count > 10_000
    assert res.sentence_count > 50
