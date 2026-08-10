from __future__ import annotations

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.config.logging import get_logger
from src.jobs.alert_watcher_job import run_alert_watcher_check
from src.jobs.daily_briefing_job import run_daily_briefing_check
from src.jobs.earnings_reminder_job import run_earnings_reminder_check

logger = get_logger(__name__)


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    # Checks every minute for users whose preferred briefing time has arrived.
    scheduler.add_job(
        run_daily_briefing_check,
        trigger=CronTrigger(minute="*"),
        args=[bot],
        id="daily_briefing_check",
        replace_existing=True,
    )

    # Checks every 5 minutes for triggered watchlist alerts (price moves, etc.)
    scheduler.add_job(
        run_alert_watcher_check,
        trigger=IntervalTrigger(minutes=5),
        args=[bot],
        id="alert_watcher_check",
        replace_existing=True,
    )

    # Checks hourly for same-day earnings on any followed ticker.
    scheduler.add_job(
        run_earnings_reminder_check,
        trigger=IntervalTrigger(hours=1),
        args=[bot],
        id="earnings_reminder_check",
        replace_existing=True,
    )

    logger.info("scheduler_configured", jobs=[job.id for job in scheduler.get_jobs()])
    return scheduler
