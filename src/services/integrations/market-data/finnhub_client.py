"""
Finnhub API client. Thin re-export — the implementation lives in
services/market_data/providers/finnhub_provider.py (that's what the
aggregator imports). See base_provider.py for why this re-export exists.
"""
from __future__ import annotations

from src.services.market_data.providers.finnhub_provider import FinnhubProvider as FinnhubClient

__all__ = ["FinnhubClient"]
