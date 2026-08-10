"""
Base provider interface. Thin re-export — the actual definitions live in
services/market_data/provider_interface.py, which is what the aggregator
and agents import. Exposed here too so the integrations/ tree (external
API clients) reads as a complete, self-contained picture on disk.
"""
from __future__ import annotations

from src.services.market_data.provider_interface import (
    CompanyProfile,
    MarketDataProvider,
    NewsItem,
    Quote,
)

__all__ = ["MarketDataProvider", "Quote", "NewsItem", "CompanyProfile"]
