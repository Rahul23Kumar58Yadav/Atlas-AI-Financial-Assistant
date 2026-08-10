"""
Long-term memory: durable facts about a user (watchlist, sectors, role,
recurring topics) that agents inject into their system prompt so answers
feel personalized without the user repeating themselves.

Preferences (structured) live in Preference; freeform facts live in
MemoryFact. This class reads both and gives agents one clean context blob.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.memory_fact import MemoryFact
from src.db.repositories.preference_repository import PreferenceRepository
from src.db.repositories.watchlist_repository import WatchlistRepository


class LongTermMemory:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.preference_repo = PreferenceRepository(session)
        self.watchlist_repo = WatchlistRepository(session)

    async def get_context_for_user(self, user_id: int) -> str:
        """Renders everything known about a user into a short paragraph for the system prompt."""
        pref = await self.preference_repo.get_for_user(user_id)
        watchlist = await self.watchlist_repo.get_symbols_for_user(user_id)
        facts = await self._get_facts(user_id)

        lines = []
        if watchlist:
            lines.append(f"Watchlist: {', '.join(watchlist)}")
        if pref:
            if pref.followed_sectors:
                lines.append(f"Follows sectors: {', '.join(pref.followed_sectors)}")
            if pref.insight_types:
                lines.append(f"Prefers insight types: {', '.join(pref.insight_types)}")
        if facts:
            lines.append("Other known preferences: " + "; ".join(f"{f.key}={f.value}" for f in facts))

        return "\n".join(lines) if lines else "No stored preferences yet — this may be a new user."

    async def _get_facts(self, user_id: int, limit: int = 20) -> list[MemoryFact]:
        result = await self.session.execute(
            select(MemoryFact).where(MemoryFact.user_id == user_id).limit(limit)
        )
        return list(result.scalars().all())

    async def add_fact(self, user_id: int, key: str, value: str, source_message_id: int | None = None):
        self.session.add(MemoryFact(user_id=user_id, key=key, value=value, source_message_id=source_message_id))

    async def has_fact(self, user_id: int, key: str) -> bool:
        """
        Checks for the existence of a specific key, e.g. a dedupe marker
        like "earnings_reminder_sent:AAPL:2026-01-29" — see
        jobs/earnings_reminder_job.py. Reuses MemoryFact as lightweight
        idempotency tracking rather than adding a dedicated table.
        """
        result = await self.session.execute(
            select(MemoryFact).where(MemoryFact.user_id == user_id, MemoryFact.key == key).limit(1)
        )
        return result.scalar_one_or_none() is not None
