"""Tests for engine/clean_screening.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.clean_screening import (
    _has_amendment_within_window,
    _load_denylist,
    _name_matches_denylist,
    screen_peer,
)
from engine.edgar import FilingRef


def test_load_denylist_parses_ciks_and_names(tmp_path: Path):
    f = tmp_path / "deny.txt"
    f.write_text(
        "# comment\n"
        "0001024401\n"
        "Enron\n"
        "\n"
        "  HEALTH south  \n"
    )
    ciks, names = _load_denylist(f)
    assert "0001024401" in ciks
    assert "enron" in names
    assert any("health south" in n for n in names)


def test_name_matches_denylist_is_case_insensitive():
    assert _name_matches_denylist("ENRON Corp", {"enron"})
    assert not _name_matches_denylist("Apple Inc", {"enron"})


def test_screen_peer_flags_aaer_denylist_cik():
    client = MagicMock()
    client.list_form_filings.return_value = []  # no 10-K/A
    res = screen_peer(
        client,
        cik="0001024401",
        company_name="Test Co",
        candidate_filing_date="2001-01-01",
        aaer_denylist=({"0001024401"}, set()),
        classaction_denylist=(set(), set()),
    )
    assert res.is_clean is False
    assert "aaer_denylist_cik" in res.flags


def test_screen_peer_flags_classaction_denylist_name():
    client = MagicMock()
    client.list_form_filings.return_value = []
    res = screen_peer(
        client,
        cik="0001234567",
        company_name="WorldCom Inc",
        candidate_filing_date="2002-03-13",
        aaer_denylist=(set(), set()),
        classaction_denylist=(set(), {"worldcom"}),
    )
    assert res.is_clean is False
    assert "classaction_denylist_name" in res.flags


def test_screen_peer_passes_clean_company():
    client = MagicMock()
    client.list_form_filings.return_value = []
    res = screen_peer(
        client,
        cik="0001234567",
        company_name="Acme Industries Inc",
        candidate_filing_date="2001-01-01",
        aaer_denylist=(set(), set()),
        classaction_denylist=(set(), set()),
    )
    assert res.is_clean is True
    assert res.flags == []


def test_amendment_within_window_finds_5y_match():
    client = MagicMock()
    client.list_form_filings.return_value = [
        FilingRef(cik="0001234567", accession="X", form="10-K/A",
                  filing_date="2003-06-15", report_date="2001-12-31",
                  primary_document="amend.txt"),
    ]
    flag, acc = _has_amendment_within_window(client, "0001234567", "2002-01-01", days=365 * 5)
    assert flag is True
    assert acc == "X"


def test_amendment_within_window_misses_outside_5y():
    client = MagicMock()
    client.list_form_filings.return_value = [
        FilingRef(cik="0001234567", accession="X", form="10-K/A",
                  filing_date="2010-06-15", report_date="2001-12-31",
                  primary_document="amend.txt"),
    ]
    flag, _ = _has_amendment_within_window(client, "0001234567", "2002-01-01", days=365 * 5)
    assert flag is False
