"""
Every market data provider implements this interface. Agents and the
aggregator only ever depend on this shape — never on a specific provider's
response format. Add SEC EDGAR, FMP, Polygon, etc. by implementing this
without touching any calling code.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Quote:
    symbol: str
    price: float
    change_percent: float
    currency: str = "USD"


@dataclass
class NewsItem:
    headline: str
    summary: str
    url: str
    published_at: str
    source: str


@dataclass
class CompanyProfile:
    symbol: str
    name: str
    sector: str | None
    industry: str | None
    market_cap: float | None
    description: str | None


class MarketDataProvider(ABC):
    name: str

    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote | None:
        ...

    @abstractmethod
    async def get_company_profile(self, symbol: str) -> CompanyProfile | None:
        ...

    @abstractmethod
    async def get_company_news(self, symbol: str, limit: int = 5) -> list[NewsItem]:
        ...
