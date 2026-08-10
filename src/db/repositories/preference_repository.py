from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.preference import Preference


class PreferenceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_for_user(self, user_id: int) -> Preference | None:
        result = await self.session.execute(select(Preference).where(Preference.user_id == user_id))
        return result.scalar_one_or_none()

    async def set_briefing_time(self, user_id: int, hour: int, minute: int, timezone: str) -> Preference:
        pref = await self.get_for_user(user_id)
        pref.briefing_hour = hour
        pref.briefing_minute = minute
        pref.timezone = timezone
        self.session.add(pref)
        return pref

    async def add_sector(self, user_id: int, sector: str) -> Preference:
        pref = await self.get_for_user(user_id)
        if sector not in pref.followed_sectors:
            pref.followed_sectors = [*pref.followed_sectors, sector]
            self.session.add(pref)
        return pref
