"""SEC EDGAR client with rate limiting and on-disk caching.

EDGAR fair-access policy requires:
  * a User-Agent header identifying the requester (name + email)
  * no more than 10 requests per second

Both are enforced here. Every successful response is cached on disk under
`data/raw/edgar/` so repeat runs are deterministic and offline-friendly.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

EDGAR_RATE_LIMIT = 10.0  # requests per second, hard ceiling per EDGAR fair-access
DEFAULT_USER_AGENT = "Arsenii Chan arseniichan9@gmail.com"
DEFAULT_CACHE_DIR = Path("data/raw/edgar")
SUBMISSIONS_BASE = "https://data.sec.gov/submissions"
ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"


def _pad_cik(cik: str | int) -> str:
    """EDGAR CIKs are 10-digit zero-padded in submissions URLs."""
    return str(int(str(cik).lstrip("0") or "0")).zfill(10)


def _strip_dashes(accession: str) -> str:
    return accession.replace("-", "")


@dataclass
class FilingRef:
    """One row from a company's submissions JSON, post-filter."""

    cik: str  # 10-digit padded
    accession: str  # with dashes, e.g. "0000950144-01-500616"
    form: str  # e.g. "10-K"
    filing_date: str  # ISO date, e.g. "2001-04-02"
    report_date: str  # period of report, ISO date
    primary_document: str  # filename of the primary 10-K doc
    primary_doc_description: str = ""

    @property
    def accession_nodash(self) -> str:
        return _strip_dashes(self.accession)

    @property
    def archive_dir_url(self) -> str:
        cik_int = int(self.cik)
        return f"{ARCHIVES_BASE}/{cik_int}/{self.accession_nodash}"

    @property
    def primary_doc_url(self) -> str:
        return f"{self.archive_dir_url}/{self.primary_document}"

    @property
    def index_url(self) -> str:
        return f"{self.archive_dir_url}/{self.accession}-index.htm"


class _RateLimiter:
    """Sliding-window limiter: at most `rate` requests per second."""

    def __init__(self, rate: float) -> None:
        self.rate = rate
        self._times: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            window = now - 1.0
            while self._times and self._times[0] < window:
                self._times.popleft()
            if len(self._times) >= self.rate:
                sleep_for = 1.0 - (now - self._times[0])
                if sleep_for > 0:
                    time.sleep(sleep_for)
                now = time.monotonic()
                window = now - 1.0
                while self._times and self._times[0] < window:
                    self._times.popleft()
            self._times.append(now)


class EdgarClient:
    """Thin EDGAR client.

    Cache layout:
      data/raw/edgar/submissions/CIK0001024401.json
      data/raw/edgar/filings/<accession_nodash>/<filename>
      data/raw/edgar/url-cache/<sha256>.<ext>   # arbitrary URLs (index pages etc.)
    """

    def __init__(
        self,
        user_agent: str | None = None,
        cache_dir: Path | str = DEFAULT_CACHE_DIR,
        rate: float = EDGAR_RATE_LIMIT,
    ) -> None:
        ua = user_agent or os.environ.get("CANARY_EDGAR_USER_AGENT", DEFAULT_USER_AGENT)
        if "@" not in ua:
            raise ValueError(
                "EDGAR User-Agent must include a contact email per fair-access policy. "
                "Set CANARY_EDGAR_USER_AGENT or pass user_agent=..."
            )
        self.user_agent = ua
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._limiter = _RateLimiter(rate)
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": ua,
                "Accept-Encoding": "gzip, deflate",
                "Host": "www.sec.gov",  # overridden per request
            }
        )

    # ---- low-level ---------------------------------------------------------

    def _get(self, url: str, *, host: str | None = None, timeout: float = 30.0) -> requests.Response:
        self._limiter.acquire()
        headers = dict(self._session.headers)
        if host:
            headers["Host"] = host
        else:
            from urllib.parse import urlparse

            headers["Host"] = urlparse(url).netloc
        resp = self._session.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp

    # ---- submissions JSON --------------------------------------------------

    def submissions(self, cik: str | int, *, force: bool = False) -> dict[str, Any]:
        """Fetch the full submissions JSON for a CIK, cached on disk.

        Returns the parsed JSON dict; caller is responsible for filtering forms.
        """
        cik_padded = _pad_cik(cik)
        cache_path = self.cache_dir / "submissions" / f"CIK{cik_padded}.json"
        if cache_path.exists() and not force:
            return json.loads(cache_path.read_text())
        url = f"{SUBMISSIONS_BASE}/CIK{cik_padded}.json"
        resp = self._get(url, host="data.sec.gov")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(resp.text)
        return resp.json()

    # ---- filing search -----------------------------------------------------

    def list_form_filings(
        self,
        cik: str | int,
        form: str | list[str] = "10-K",
    ) -> list[FilingRef]:
        """Return all filings of `form` (or any form in a list) for the given CIK.

        EDGAR distinguishes 10-K from 10-K405 (a discontinued pre-2003 variant —
        substantively the same annual report). Callers wanting both should pass
        a list, e.g. ``["10-K", "10-K405"]``.
        """
        sub = self.submissions(cik)
        recent = sub.get("filings", {}).get("recent", {})
        rows = list(
            zip(
                recent.get("accessionNumber", []),
                recent.get("form", []),
                recent.get("filingDate", []),
                recent.get("reportDate", []),
                recent.get("primaryDocument", []),
                recent.get("primaryDocDescription", []),
                strict=False,
            )
        )
        # Older filings may live in additional files referenced by `filings.files`.
        for entry in sub.get("filings", {}).get("files", []):
            extra_url = f"{SUBMISSIONS_BASE}/{entry['name']}"
            cache_path = self.cache_dir / "submissions" / entry["name"]
            if cache_path.exists():
                extra = json.loads(cache_path.read_text())
            else:
                resp = self._get(extra_url, host="data.sec.gov")
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(resp.text)
                extra = resp.json()
            rows.extend(
                zip(
                    extra.get("accessionNumber", []),
                    extra.get("form", []),
                    extra.get("filingDate", []),
                    extra.get("reportDate", []),
                    extra.get("primaryDocument", []),
                    extra.get("primaryDocDescription", []),
                    strict=False,
                )
            )

        cik_padded = _pad_cik(cik)
        accepted = {form} if isinstance(form, str) else set(form)
        out: list[FilingRef] = []
        for acc, frm, fdate, rdate, doc, desc in rows:
            if frm not in accepted:
                continue
            out.append(
                FilingRef(
                    cik=cik_padded,
                    accession=acc,
                    form=frm,
                    filing_date=fdate,
                    report_date=rdate,
                    primary_document=doc,
                    primary_doc_description=desc or "",
                )
            )
        return out

    DEFAULT_10K_FORMS = ("10-K", "10-K405")

    def find_10k_for_fiscal_year(
        self,
        cik: str | int,
        fiscal_year: int,
        forms: tuple[str, ...] | None = None,
    ) -> FilingRef | None:
        """Return the annual report whose period-of-report ends in the given fiscal year.

        Default form list is ``("10-K", "10-K405")``. 10-K405 was a pre-2003 variant
        with the same substantive content as a 10-K (the trailing 405 just indicated
        section 16(b) reporting compliance). WorldCom's FY2001 annual report is filed
        as 10-K405 — without it, you can't pin that accession.

        Most issuers have calendar-year fiscal years, so we match by the year component
        of `reportDate` (period of report). When multiple matches exist (rare — usually
        a 10-K and a 10-K/A) the earliest filing_date is preferred; callers wanting an
        amendment should query ``list_form_filings(cik, "10-K/A")`` directly.
        """
        forms = forms or self.DEFAULT_10K_FORMS
        candidates = [
            f for f in self.list_form_filings(cik, list(forms))
            if f.report_date and f.report_date.startswith(str(fiscal_year))
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda f: f.filing_date)
        return candidates[0]

    # ---- document download -------------------------------------------------

    def fetch_filing_document(self, filing: FilingRef, *, force: bool = False) -> Path:
        """Download the primary document for a filing into the cache. Returns the path."""
        out_dir = self.cache_dir / "filings" / filing.accession_nodash
        out_path = out_dir / filing.primary_document
        if out_path.exists() and not force:
            return out_path
        out_dir.mkdir(parents=True, exist_ok=True)
        resp = self._get(filing.primary_doc_url, host="www.sec.gov")
        out_path.write_bytes(resp.content)
        return out_path

    def fetch_url(self, url: str, *, host: str | None = None, force: bool = False) -> bytes:
        """Generic GET with on-disk caching keyed by URL hash."""
        h = hashlib.sha256(url.encode()).hexdigest()
        ext = url.rsplit(".", 1)[-1] if "." in url.rsplit("/", 1)[-1] else "bin"
        cache_path = self.cache_dir / "url-cache" / f"{h}.{ext}"
        if cache_path.exists() and not force:
            return cache_path.read_bytes()
        resp = self._get(url, host=host)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(resp.content)
        return resp.content
