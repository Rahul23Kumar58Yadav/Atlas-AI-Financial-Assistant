"""
Feature-oriented facade for everything the assistant knows about a user:
watchlist, sectors, insight preferences, and freeform learned facts.
Wraps PreferenceRepository + LongTermMemory so other services don't need
to know the difference between "structured preference" and "freeform
memory fact" storage.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.memory.long_term_memory import LongTermMemory
from src.db.repositories.preference_repository import PreferenceRepository
from src.db.repositories.watchlist_repository import WatchlistRepository


class PersonalizationService:
    async def get_context(self, session: AsyncSession, user_id: int) -> str:
        """Rendered natural-language summary of what's known about a user — for system prompts."""
        memory = LongTermMemory(session)
        return await memory.get_context_for_user(user_id)

    async def add_to_watchlist(self, session: AsyncSession, user_id: int, ticker: str):
        repo = WatchlistRepository(session)
        return await repo.add(user_id, ticker)

    async def get_watchlist(self, session: AsyncSession, user_id: int) -> list[str]:
        repo = WatchlistRepository(session)
        return await repo.get_symbols_for_user(user_id)

    async def follow_sector(self, session: AsyncSession, user_id: int, sector: str):
        repo = PreferenceRepository(session)
        return await repo.add_sector(user_id, sector)

    async def set_briefing_schedule(self, session: AsyncSession, user_id: int, hour: int, minute: int, timezone: str = "UTC"):
        repo = PreferenceRepository(session)
        return await repo.set_briefing_time(user_id, hour, minute, timezone)

    async def learn_fact(self, session: AsyncSession, user_id: int, key: str, value: str, source_message_id: int | None = None):
        """
        Persist a freeform fact picked up mid-conversation — e.g. the user
        mentions they're a value investor, or that they always check
        pre-market before the open. Doesn't fit the fixed Preference schema,
        so it goes to MemoryFact instead.
        """
        memory = LongTermMemory(session)
        await memory.add_fact(user_id, key, value, source_message_id)

    async def get_preferences(self, session: AsyncSession, user_id: int):
        repo = PreferenceRepository(session)
        return await repo.get_for_user(user_id)


personalization_service = PersonalizationService()
