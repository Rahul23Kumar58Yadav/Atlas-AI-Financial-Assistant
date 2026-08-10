from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.preference import Preference
from src.db.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_or_create(
        self, telegram_id: int, username: str | None, first_name: str | None
    ) -> tuple[User, bool]:
        """Returns (user, created). Also creates an empty Preference row for new users."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            return user, False

        user = User(telegram_id=telegram_id, telegram_username=username, first_name=first_name)
        self.session.add(user)
        await self.session.flush()  # need user.id before creating Preference

        self.session.add(Preference(user_id=user.id))
        await self.session.flush()

        return user, True

    async def mark_onboarding_step(self, user: User, step: str | None, completed: bool = False) -> None:
        user.onboarding_step = step
        user.onboarding_completed = completed
        self.session.add(user)
