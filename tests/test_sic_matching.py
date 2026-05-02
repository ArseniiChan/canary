"""Tests for engine/sic_matching.py — only the pure-logic parsing helpers.

Network-touching functions are exercised in smoke tests rather than unit tests.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.sic_matching import _parse_company_listing, companies_with_sic2


def test_parse_company_listing_handles_empty():
    assert _parse_company_listing("<html><body>nothing</body></html>") == []


def test_parse_company_listing_extracts_cik_and_name():
    html = """
    <html><body><table class="tableFile2">
      <tr><th>CIK</th><th>Name</th></tr>
      <tr><td><a href="/cgi-bin/browse-edgar?action=getcompany&CIK=0001024401">0001024401</a></td>
          <td>ENRON CORP/OR/</td></tr>
      <tr><td><a href="/cgi-bin/browse-edgar?action=getcompany&CIK=0000806085">0000806085</a></td>
          <td>LEHMAN BROTHERS HOLDINGS INC</td></tr>
    </table></body></html>
    """
    out = _parse_company_listing(html)
    assert len(out) == 2
    ciks = {c.cik for c in out}
    assert "0001024401" in ciks
    assert "0000806085" in ciks
    names = {c.name for c in out}
    assert "ENRON CORP/OR/" in names


def test_companies_with_sic2_validates_input():
    with pytest.raises(ValueError):
        companies_with_sic2(client=None, sic2="6")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        companies_with_sic2(client=None, sic2="abc")  # type: ignore[arg-type]
