"""
Short-term memory: recent conversation turns, formatted for direct use
as LLM message history. Backed by the flat Message table — no separate
cache needed at hackathon scale.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.repositories.conversation_repository import ConversationRepository


class ConversationMemory:
    def __init__(self, session: AsyncSession):
        self.repo = ConversationRepository(session)

    async def get_history_for_llm(self, user_id: int, limit: int = 20) -> list[dict]:
        messages = await self.repo.get_recent(user_id, limit=limit)
        return [{"role": m.role, "content": m.content} for m in messages]

    async def record_turn(self, user_id: int, user_text: str, assistant_text: str, intent: str | None = None):
        await self.repo.add_message(user_id, role="user", content=user_text, intent=intent)
        await self.repo.add_message(user_id, role="assistant", content=assistant_text)
