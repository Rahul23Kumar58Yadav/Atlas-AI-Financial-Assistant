"""
Single entrypoint agents call for market data. Currently backed by one
provider (Finnhub); add more to `self.providers` and pick/merge here
without changing any agent code.
"""
from __future__ import annotations

from src.services.market_data.provider_interface import CompanyProfile, NewsItem, Quote
from src.services.market_data.providers.finnhub_provider import FinnhubProvider


class MarketDataAggregator:
    def __init__(self):
        self.primary = FinnhubProvider()

    async def get_quote(self, symbol: str) -> Quote | None:
        return await self.primary.get_quote(symbol)

    async def get_company_profile(self, symbol: str) -> CompanyProfile | None:
        return await self.primary.get_company_profile(symbol)

    async def get_company_news(self, symbol: str, limit: int = 5) -> list[NewsItem]:
        return await self.primary.get_company_news(symbol, limit=limit)

    async def get_earnings_calendar(self, symbol: str, days_ahead: int = 7) -> list[dict]:
        return await self.primary.get_earnings_calendar(symbol, days_ahead=days_ahead)

    async def get_company_snapshot(self, symbol: str) -> dict:
        """Convenience bundle used by research_agent and briefing_agent."""
        quote = await self.get_quote(symbol)
        profile = await self.get_company_profile(symbol)
        news = await self.get_company_news(symbol, limit=3)

        return {
            "symbol": symbol.upper(),
            "quote": quote.__dict__ if quote else None,
            "profile": profile.__dict__ if profile else None,
            "recent_news": [n.__dict__ for n in news],
        }


market_data = MarketDataAggregator()
