"""Probe browse-edgar to learn what SIC parameter forms work."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from bs4 import BeautifulSoup

from engine.edgar import EdgarClient

client = EdgarClient()

PROBES = [
    ("62", "two-digit prefix"),
    ("6200", "four-digit exact"),
    ("6211", "four-digit exact (Lehman's SIC)"),
    ("48", "two-digit prefix for telecom"),
    ("4813", "four-digit exact for WorldCom's SIC"),
]

for sic, label in PROBES:
    url = (
        "https://www.sec.gov/cgi-bin/browse-edgar"
        f"?action=getcompany&SIC={sic}&type=10-K&dateb=&owner=include&count=40&start=0"
    )
    body = client.fetch_url(url, host="www.sec.gov")
    soup = BeautifulSoup(body.decode("utf-8", errors="replace"), "lxml")
    table = soup.find("table", class_="tableFile2")
    company_rows = []
    if table:
        for tr in table.find_all("tr"):
            link = tr.find("a", href=re.compile(r"CIK=\d+"))
            if link:
                m = re.search(r"CIK=(\d+)", link["href"])
                tds = tr.find_all("td")
                if m and tds:
                    name = tds[1].get_text(strip=True) if len(tds) > 1 else "?"
                    company_rows.append((m.group(1), name))
    # Page header sometimes includes the SIC description
    h_text = ""
    for tag_name in ("h1", "h2", "h3", "h4"):
        for h in soup.find_all(tag_name):
            txt = h.get_text(strip=True)
            if "SIC" in txt or "Industry" in txt:
                h_text = txt
                break
        if h_text:
            break
    print(f"\nSIC={sic!s:<5}  ({label})")
    print(f"  header: {h_text[:120] if h_text else '<none>'}")
    print(f"  table rows: {len(company_rows)}")
    for cik, name in company_rows[:5]:
        print(f"    CIK={cik:>10}  {name[:80]}")

    # Look for "Showing N of M" hint
    text = soup.get_text(" ", strip=True)
    m = re.search(r"Items\s+\d+\s*-\s*\d+\s+of\s+\d+", text)
    if m:
        print(f"  pagination hint: {m.group(0)}")
