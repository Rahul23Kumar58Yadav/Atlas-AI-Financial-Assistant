"""
Feature-oriented facade over onboarding. The actual state machine and
prompts live in services/personalization/onboarding.py (prompts are
defined in services/ai/prompts/onboarding_prompt.py) — this file exposes
that as one clean service so bot handlers depend on
"services.onboarding_service" rather than reaching into personalization/
internals directly.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.user import User
from src.services.personalization.onboarding import (
    get_next_onboarding_prompt,
    process_onboarding_reply,
)


class OnboardingService:
    async def get_next_prompt(self, session: AsyncSession, user: User) -> str:
        return await get_next_onboarding_prompt(session, user)

    async def process_reply(self, session: AsyncSession, user: User, reply_text: str) -> str:
        return await process_onboarding_reply(session, user, reply_text)

    def is_complete(self, user: User) -> bool:
        return user.onboarding_completed


onboarding_service = OnboardingService()
