"""
Feature-oriented facade for morning/evening briefs. Owns the actual
business logic (who's due for a brief right now, whether it's worth
sending) — jobs/daily_briefing_job.py becomes a thin scheduler trigger
that just calls send_due_briefings() on a timer.
"""
from __future__ import annotations

import datetime as dt

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.logging import get_logger
from src.core.agents.briefing_agent import build_daily_briefing
from src.db.models.preference import Preference
from src.db.models.user import User
from src.db.repositories.watchlist_repository import WatchlistRepository

logger = get_logger(__name__)


class BriefingService:
    async def get_users_due_now(self, session: AsyncSession, now: dt.datetime | None = None) -> list[tuple[User, Preference]]:
        """
        Users whose preferred briefing time matches the current minute.
        MVP: compares against UTC directly — `Preference.timezone` is stored
        but not yet applied here; convert `now` per-user timezone (zoneinfo)
        before comparing hour/minute for a real multi-timezone deployment.
        """
        now = now or dt.datetime.utcnow()

        result = await session.execute(
            select(User, Preference)
            .join(Preference, Preference.user_id == User.id)
            .where(
                Preference.briefing_hour == now.hour,
                Preference.briefing_minute == now.minute,
                User.onboarding_completed.is_(True),
            )
        )
        return list(result.all())

    async def build_brief_for(self, session: AsyncSession, user_id: int) -> str | None:
        """Returns None when nothing's noteworthy — a valid, expected outcome, not an error."""
        watchlist_repo = WatchlistRepository(session)
        watchlist = await watchlist_repo.get_symbols_for_user(user_id)
        return await build_daily_briefing(watchlist)

    async def send_due_briefings(self, session: AsyncSession, bot: Bot, now: dt.datetime | None = None) -> int:
        """Returns the count of briefs actually sent, for logging/testing."""
        due = await self.get_users_due_now(session, now)
        sent_count = 0

        for user, _preference in due:
            try:
                brief = await self.build_brief_for(session, user.id)
                if brief is None:
                    logger.info("briefing_skipped_nothing_notable", user_id=user.id)
                    continue

                await bot.send_message(user.telegram_id, brief)
                sent_count += 1
                logger.info("briefing_sent", user_id=user.id)
            except Exception as exc:  # noqa: BLE001 — one user's failure shouldn't stop the batch
                logger.error("briefing_failed", user_id=user.id, error=str(exc))

        return sent_count


briefing_service = BriefingService()
