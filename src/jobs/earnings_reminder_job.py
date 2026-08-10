"""
Checks each user's watchlist against Finnhub's earnings calendar and sends
a one-time reminder on the day a followed company reports.

Honest limitation: Finnhub's free tier gives a date + session ("bmo"/"amc"/
"dmh"), not an exact timestamp, so this can't do "remind me exactly 1 hour
before" as literally described in the hackathon brief — it reminds once,
the morning a followed company is reporting, and says which session.
Swapping in a provider with exact timestamps (many paid tiers have this)
would let this become a precise pre-call reminder without changing the
dedup/sending logic below.
"""
from __future__ import annotations

import datetime as dt

from aiogram import Bot
from sqlalchemy import select

from src.config.logging import get_logger
from src.core.memory.long_term_memory import LongTermMemory
from src.db.base import get_session
from src.db.models.user import User
from src.db.repositories.watchlist_repository import WatchlistRepository
from src.services.market_data.aggregator import market_data

logger = get_logger(__name__)

_SESSION_LABELS = {
    "bmo": "before market open",
    "amc": "after market close",
    "dmh": "during market hours",
}


def _dedupe_key(symbol: str, date: str) -> str:
    return f"earnings_reminder_sent:{symbol}:{date}"


async def run_earnings_reminder_check(bot: Bot) -> None:
    today = dt.date.today().isoformat()
    reminders_sent = 0

    async with get_session() as session:
        # Every onboarded user — reused pattern from briefing_service, but this
        # doesn't filter by time-of-day since "reports today" only needs checking once.
        result = await session.execute(select(User).where(User.onboarding_completed.is_(True)))
        users = list(result.scalars().all())

        for user in users:
            watchlist_repo = WatchlistRepository(session)
            memory = LongTermMemory(session)
            symbols = await watchlist_repo.get_symbols_for_user(user.id)

            for symbol in symbols:
                try:
                    earnings = await market_data.get_earnings_calendar(symbol, days_ahead=1)
                except Exception as exc:  # noqa: BLE001 — one symbol's failure shouldn't block the rest
                    logger.error("earnings_calendar_fetch_failed", symbol=symbol, error=str(exc))
                    continue

                for entry in earnings:
                    if entry.get("date") != today:
                        continue

                    key = _dedupe_key(symbol, today)
                    if await memory.has_fact(user.id, key):
                        continue

                    session_label = _SESSION_LABELS.get(entry.get("hour"), "today")
                    message = f"{symbol} reports earnings today ({session_label})."
                    if entry.get("eps_estimate") is not None:
                        message += f" Analyst EPS estimate: {entry['eps_estimate']}."

                    try:
                        await bot.send_message(user.telegram_id, message)
                        await memory.add_fact(user.id, key, value="sent")
                        reminders_sent += 1
                        logger.info("earnings_reminder_sent", user_id=user.id, symbol=symbol)
                    except Exception as exc:  # noqa: BLE001
                        logger.error("earnings_reminder_send_failed", user_id=user.id, symbol=symbol, error=str(exc))

    if reminders_sent:
        logger.info("earnings_reminder_batch_complete", reminders_sent=reminders_sent)
