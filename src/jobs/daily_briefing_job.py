"""
Thin scheduler trigger. All the actual logic (who's due, whether the brief
is worth sending) lives in services/briefing_service.py — this file's only
job is to open a session and hand off to the service on the schedule
jobs/scheduler.py configures.
"""
from __future__ import annotations

from aiogram import Bot

from src.config.logging import get_logger
from src.db.base import get_session
from src.services.briefing_service import briefing_service

logger = get_logger(__name__)


async def run_daily_briefing_check(bot: Bot) -> None:
    async with get_session() as session:
        sent_count = await briefing_service.send_due_briefings(session, bot)
        if sent_count:
            logger.info("briefing_batch_complete", sent_count=sent_count)
