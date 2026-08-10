"""
SEC EDGAR client. Free, no API key — but the SEC requires every request to
carry an identifying User-Agent (name + contact email), or it will start
returning 403s. Set SEC_EDGAR_USER_AGENT in .env before using this in
anything beyond local testing.

Two-step lookup, matching how EDGAR's data API actually works:
  1. ticker -> CIK (from the company_tickers.json index, cached in-process)
  2. CIK -> recent filings (from the submissions endpoint)
"""
from __future__ import annotations

import httpx

from src.config.logging import get_logger
from src.config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()

TICKER_INDEX_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

# Simple in-process cache — the ticker->CIK index is ~large and changes rarely.
_ticker_to_cik_cache: dict[str, str] | None = None


class SECEdgarClient:
    def __init__(self, user_agent: str | None = None):
        self.user_agent = user_agent or settings.sec_edgar_user_agent
        self.headers = {"User-Agent": self.user_agent}

    async def _get_ticker_index(self) -> dict[str, str]:
        global _ticker_to_cik_cache
        if _ticker_to_cik_cache is not None:
            return _ticker_to_cik_cache

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(TICKER_INDEX_URL, headers=self.headers)
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPError as exc:
                logger.error("sec_edgar_ticker_index_failed", error=str(exc))
                return {}

        # data["fields"] = ["cik", "name", "ticker", "exchange"]; data["data"] is rows
        index: dict[str, str] = {}
        for row in data.get("data", []):
            cik, _name, ticker, _exchange = row[0], row[1], row[2], row[3]
            index[ticker.upper()] = str(cik).zfill(10)

        _ticker_to_cik_cache = index
        return index

    async def get_cik_for_ticker(self, ticker: str) -> str | None:
        index = await self._get_ticker_index()
        return index.get(ticker.upper())

    async def get_recent_filings(self, ticker: str, limit: int = 5, form_type: str | None = None) -> list[dict]:
        """
        Returns recent filings for a company, e.g.:
        [{"form": "10-Q", "filed_at": "2025-11-01", "accession_number": "...", "primary_document_url": "..."}]

        `form_type` optionally filters to a specific form, e.g. "10-K", "8-K".
        """
        cik = await self.get_cik_for_ticker(ticker)
        if not cik:
            logger.warning("sec_edgar_no_cik", ticker=ticker)
            return []

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(SUBMISSIONS_URL.format(cik=cik), headers=self.headers)
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPError as exc:
                logger.error("sec_edgar_submissions_failed", ticker=ticker, error=str(exc))
                return []

        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accession_numbers = recent.get("accessionNumber", [])
        primary_documents = recent.get("primaryDocument", [])

        filings = []
        for i in range(len(forms)):
            if form_type and forms[i] != form_type:
                continue

            accession_no_dashes = accession_numbers[i].replace("-", "")
            doc_url = (
                f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
                f"{accession_no_dashes}/{primary_documents[i]}"
            )

            filings.append(
                {
                    "form": forms[i],
                    "filed_at": dates[i],
                    "accession_number": accession_numbers[i],
                    "primary_document_url": doc_url,
                }
            )

            if len(filings) >= limit:
                break

        return filings
