"""
Seeds the local dev DB with a sample user, watchlist, alert, and a couple
of conversation turns — so you're not staring at an empty bot on first run.

Usage:
    python -m scripts.seed_db
    python -m scripts.seed_db --telegram-id 123456789
"""
from __future__ import annotations

import argparse
import asyncio

from src.config.logging import configure_logging, get_logger
from src.db.base import get_session, init_db
from src.db.repositories.alert_repository import AlertRepository
from src.db.repositories.conversation_repository import ConversationRepository
from src.db.repositories.preference_repository import PreferenceRepository
from src.db.repositories.user_repository import UserRepository
from src.db.repositories.watchlist_repository import WatchlistRepository

logger = get_logger(__name__)


async def seed(telegram_id: int) -> None:
    await init_db()

    async with get_session() as session:
        user_repo = UserRepository(session)
        user, created = await user_repo.get_or_create(telegram_id=telegram_id, username="demo_user", first_name="Demo")
        user.role = "Investor"
        await user_repo.mark_onboarding_step(user, step="done", completed=True)
        session.add(user)

        pref_repo = PreferenceRepository(session)
        await pref_repo.set_briefing_time(user.id, hour=8, minute=0, timezone="UTC")
        pref = await pref_repo.get_for_user(user.id)
        pref.followed_sectors = ["semiconductors", "AI"]
        pref.insight_types = ["earnings", "filings", "market_news"]
        session.add(pref)

        watchlist_repo = WatchlistRepository(session)
        for symbol, note in [("AAPL", None), ("NVDA", "AI exposure"), ("TSLA", "earnings watch")]:
            await watchlist_repo.add(user.id, symbol, note=note)

        alert_repo = AlertRepository(session)
        await alert_repo.create(user.id, symbol="TSLA", threshold_percent=5.0)

        conv_repo = ConversationRepository(session)
        await conv_repo.add_message(user.id, role="user", content="What's happening with NVDA today?", intent="research")
        await conv_repo.add_message(
            user.id,
            role="assistant",
            content="NVDA is up modestly today on continued AI demand optimism ahead of next month's earnings.",
        )

        logger.info(
            "seed_complete",
            telegram_id=telegram_id,
            user_created=created,
            watchlist=["AAPL", "NVDA", "TSLA"],
            alerts=1,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the local dev DB with sample data")
    parser.add_argument("--telegram-id", type=int, default=100000, help="Telegram ID to seed as (default: 100000)")
    args = parser.parse_args()

    configure_logging()
    asyncio.run(seed(args.telegram_id))


if __name__ == "__main__":
    main()
