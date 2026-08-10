"""
Conversational onboarding — a small state machine, not a form. Each step
is one natural question; the user can answer freely (parsed by a quick LLM
call) or skip by saying so. No inline buttons, per the brief's constraint.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.user import User
from src.db.repositories.preference_repository import PreferenceRepository
from src.db.repositories.user_repository import UserRepository
from src.db.repositories.watchlist_repository import WatchlistRepository
from src.services.ai.llm_client import LLMClient
from src.services.ai.prompts.onboarding_prompt import (
    ONBOARDING_EXTRACTION_PROMPT as EXTRACTION_PROMPT,
    ONBOARDING_PROMPTS as PROMPTS,
    ONBOARDING_STEPS as STEPS,
)

llm = LLMClient()


async def get_next_onboarding_prompt(session: AsyncSession, user: User) -> str:
    step = user.onboarding_step or STEPS[0]
    return PROMPTS[step]


async def process_onboarding_reply(session: AsyncSession, user: User, reply_text: str) -> str:
    user_repo = UserRepository(session)
    pref_repo = PreferenceRepository(session)

    current_step = user.onboarding_step or STEPS[0]
    await _apply_answer(session, pref_repo, user, current_step, reply_text)

    next_index = STEPS.index(current_step) + 1
    next_step = STEPS[next_index]
    completed = next_step == "done"

    await user_repo.mark_onboarding_step(user, step=next_step, completed=completed)
    return PROMPTS[next_step]


async def _apply_answer(session: AsyncSession, pref_repo: PreferenceRepository, user: User, step: str, reply_text: str) -> None:
    if step == "role":
        value = await _extract(PROMPTS["role"], reply_text)
        if value:
            user.role = value
            session.add(user)
        return

    if step == "watchlist":
        value = await _extract(PROMPTS["watchlist"], reply_text)
        if value:
            watchlist_repo = WatchlistRepository(session)
            for ticker_or_topic in value.split(","):
                await watchlist_repo.add(user.id, ticker_or_topic.strip())
        return

    if step == "insight_types":
        value = await _extract(PROMPTS["insight_types"], reply_text)
        if value:
            pref = await pref_repo.get_for_user(user.id)
            pref.insight_types = [v.strip() for v in value.split(",")]
            session.add(pref)
        return

    if step == "briefing_time":
        value = await _extract(PROMPTS["briefing_time"], reply_text)
        if value:
            hour, minute = _parse_time(value)
            await pref_repo.set_briefing_time(user.id, hour, minute, timezone="UTC")
        return


async def _extract(question: str, reply: str) -> str | None:
    response = await llm.complete(
        system="You extract structured onboarding answers.",
        messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(question=question, reply=reply)}],
        max_tokens=60,
    )
    text = response.text.strip()
    return None if text.upper() == "SKIP" else text


def _parse_time(value: str) -> tuple[int, int]:
    """Very small best-effort parser for things like '8am', '7:30pm'. Falls back to 8:00."""
    import re

    match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", value.lower())
    if not match:
        return 8, 0

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    meridiem = match.group(3)

    if meridiem == "pm" and hour != 12:
        hour += 12
    if meridiem == "am" and hour == 12:
        hour = 0

    return hour, minute
