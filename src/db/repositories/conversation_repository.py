from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.conversation import Message


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_message(self, user_id: int, role: str, content: str, intent: str | None = None) -> Message:
        message = Message(user_id=user_id, role=role, content=content, intent=intent)
        self.session.add(message)
        await self.session.flush()
        return message

    async def get_recent(self, user_id: int, limit: int = 20) -> list[Message]:
        """Most recent N messages, returned oldest-first (ready to feed straight to the LLM)."""
        result = await self.session.execute(
            select(Message).where(Message.user_id == user_id).order_by(desc(Message.created_at)).limit(limit)
        )
        messages = list(result.scalars().all())
        return list(reversed(messages))
