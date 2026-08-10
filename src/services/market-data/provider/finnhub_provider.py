from __future__ import annotations

import httpx

from src.config.logging import get_logger
from src.config.settings import get_settings
from src.services.market_data.provider_interface import (
    CompanyProfile,
    MarketDataProvider,
    NewsItem,
    Quote,
)

logger = get_logger(__name__)
settings = get_settings()

BASE_URL = "https://finnhub.io/api/v1"


class FinnhubProvider(MarketDataProvider):
    name = "finnhub"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.finnhub_api_key
        if not self.api_key:
            logger.warning("finnhub_no_api_key", msg="FinnhubProvider initialized without an API key")

    async def _get(self, path: str, params: dict) -> dict | list | None:
        params = {**params, "token": self.api_key}
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(f"{BASE_URL}{path}", params=params)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPError as exc:
                logger.error("finnhub_request_failed", path=path, error=str(exc))
                return None

    async def get_quote(self, symbol: str) -> Quote | None:
        data = await self._get("/quote", {"symbol": symbol})
        if not data or data.get("c") in (None, 0):
            return None
        current, prev_close = data["c"], data.get("pc", data["c"])
        change_pct = ((current - prev_close) / prev_close * 100) if prev_close else 0.0
        return Quote(symbol=symbol.upper(), price=current, change_percent=round(change_pct, 2))

    async def get_company_profile(self, symbol: str) -> CompanyProfile | None:
        data = await self._get("/stock/profile2", {"symbol": symbol})
        if not data or not data.get("name"):
            return None
        return CompanyProfile(
            symbol=symbol.upper(),
            name=data.get("name"),
            sector=data.get("finnhubIndustry"),
            industry=data.get("finnhubIndustry"),
            market_cap=data.get("marketCapitalization"),
            description=None,
        )

    async def get_company_news(self, symbol: str, limit: int = 5) -> list[NewsItem]:
        import datetime as dt

        to_date = dt.date.today()
        from_date = to_date - dt.timedelta(days=7)
        data = await self._get(
            "/company-news",
            {"symbol": symbol, "from": from_date.isoformat(), "to": to_date.isoformat()},
        )
        if not data:
            return []

        items = []
        for entry in data[:limit]:
            items.append(
                NewsItem(
                    headline=entry.get("headline", ""),
                    summary=entry.get("summary", ""),
                    url=entry.get("url", ""),
                    published_at=str(entry.get("datetime", "")),
                    source=entry.get("source", "finnhub"),
                )
            )
        return items

    async def get_earnings_calendar(self, symbol: str, days_ahead: int = 7) -> list[dict]:
        """
        Upcoming earnings dates for a symbol, e.g.:
        [{"symbol": "AAPL", "date": "2026-01-29", "hour": "amc", "eps_estimate": 2.35}]

        `hour` is one of "bmo" (before market open), "amc" (after market
        close), or "dmh" (during market hours) — Finnhub's free tier gives
        the date and session, not an exact timestamp, so
        jobs/earnings_reminder_job.py reminds same-day rather than N hours before.
        """
        import datetime as dt

        from_date = dt.date.today()
        to_date = from_date + dt.timedelta(days=days_ahead)

        data = await self._get(
            "/calendar/earnings",
            {"from": from_date.isoformat(), "to": to_date.isoformat(), "symbol": symbol},
        )
        if not data:
            return []

        entries = data.get("earningsCalendar", [])
        return [
            {
                "symbol": entry.get("symbol", symbol.upper()),
                "date": entry.get("date"),
                "hour": entry.get("hour"),
                "eps_estimate": entry.get("epsEstimate"),
            }
            for entry in entries
        ]
