"""
Composes the proactive daily/evening brief from a user's watchlist.

Critical behavior per the brief: if nothing meaningful happened, this
returns None and the caller (daily_briefing_job) simply doesn't send a
message. Quality over frequency — silence is a valid, expected result.
"""
from __future__ import annotations

from src.services.ai.llm_client import LLMClient
from src.services.ai.prompts.briefing_prompt import BRIEFING_SYSTEM_PROMPT, NOTHING_NOTEWORTHY_SENTINEL
from src.services.market_data.aggregator import market_data

llm = LLMClient()


async def build_daily_briefing(watchlist: list[str]) -> str | None:
    if not watchlist:
        return None

    snapshots = []
    for symbol in watchlist:
        snapshot = await market_data.get_company_snapshot(symbol)
        snapshots.append(snapshot)

    response = await llm.complete(
        system=BRIEFING_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": str(snapshots)}],
        max_tokens=400,
    )

    text = response.text.strip()
    if text == NOTHING_NOTEWORTHY_SENTINEL or not text:
        return None
    return text
