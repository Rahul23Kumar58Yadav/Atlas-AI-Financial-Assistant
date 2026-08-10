"""
Thin scheduler trigger for watchlist alerts. All the actual evaluation
logic lives in services/alert_service.py — register this on a schedule
in jobs/scheduler.py (e.g. every 5 minutes) once you want alerts live.
"""
from __future__ import annotations

from aiogram import Bot

from src.config.logging import get_logger
from src.services.alert_service import alert_service

logger = get_logger(__name__)


async def run_alert_watcher_check(bot: Bot) -> None:
    triggered_count = await alert_service.check_all_alerts(bot)
    if triggered_count:
        logger.info("alert_watch_complete", triggered_count=triggered_count)
