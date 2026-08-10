"""
Feature-oriented facade for company/market research. Wraps the research
agent (LLM + tool-calling) and the raw market data aggregator so callers
have one place to go for "give me research on X" regardless of whether
they need the full conversational answer or just structured data.
"""
from __future__ import annotations

from src.core.agents.research_agent import handle_research_request
from src.services.market_data.aggregator import market_data


class ResearchService:
    async def answer(self, question: str, conversation_history: list[dict], user_context: str) -> str:
        """Full conversational research answer, with live tool-calling under the hood."""
        return await handle_research_request(question, conversation_history, user_context)

    async def get_snapshot(self, symbol: str) -> dict:
        """Raw structured data — quote + profile + news — for callers that don't need prose."""
        return await market_data.get_company_snapshot(symbol)

    async def compare_companies(self, symbols: list[str], criteria: str, user_context: str = "") -> str:
        """
        Convenience wrapper for comparison-style requests
        (e.g. "compare Microsoft and Google on revenue growth and valuation").
        Pulls a snapshot per company, then lets the research agent reason over all of them at once.
        """
        snapshots = {symbol: await self.get_snapshot(symbol) for symbol in symbols}
        prompt = (
            f"Compare {', '.join(symbols)} based on: {criteria}.\n\n"
            f"Live data for each company: {snapshots}"
        )
        return await handle_research_request(prompt, conversation_history=[], user_context=user_context)


research_service = ResearchService()
