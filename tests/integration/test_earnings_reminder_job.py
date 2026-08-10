import datetime as dt
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import src.jobs.earnings_reminder_job as job_mod
from src.db.repositories.watchlist_repository import WatchlistRepository


def _session_patch(db_session):
    """check_all_alerts/run_earnings_reminder_check open their own session via
    get_session(); point that at the same in-memory test DB instead of the
    real file-based one."""

    @asynccontextmanager
    async def _use_test_session():
        yield db_session

    return _use_test_session


async def test_sends_reminder_on_earnings_day(db_session, sample_user, fake_bot):
    watchlist_repo = WatchlistRepository(db_session)
    await watchlist_repo.add(sample_user.id, "AAPL")
    await db_session.commit()

    today = dt.date.today().isoformat()

    with patch.object(
        job_mod.market_data, "get_earnings_calendar",
        new=AsyncMock(return_value=[{"symbol": "AAPL", "date": today, "hour": "amc", "eps_estimate": 2.35}]),
    ), patch("src.jobs.earnings_reminder_job.get_session", side_effect=_session_patch(db_session)):
        await job_mod.run_earnings_reminder_check(fake_bot)

    assert len(fake_bot.sent_messages) == 1
    assert "AAPL reports earnings today (after market close)" in fake_bot.sent_messages[0][1]
    assert "2.35" in fake_bot.sent_messages[0][1]


async def test_does_not_resend_same_day_reminder(db_session, sample_user, fake_bot):
    """
    Regression test for exactly the bug caught during manual testing: the
    dedup marker (via MemoryFact) must actually prevent a second send on
    a second run for the same symbol+date.
    """
    watchlist_repo = WatchlistRepository(db_session)
    await watchlist_repo.add(sample_user.id, "AAPL")
    await db_session.commit()

    today = dt.date.today().isoformat()

    with patch.object(
        job_mod.market_data, "get_earnings_calendar",
        new=AsyncMock(return_value=[{"symbol": "AAPL", "date": today, "hour": "amc", "eps_estimate": 2.35}]),
    ), patch("src.jobs.earnings_reminder_job.get_session", side_effect=_session_patch(db_session)):
        await job_mod.run_earnings_reminder_check(fake_bot)
        await job_mod.run_earnings_reminder_check(fake_bot)  # second run, same day

    assert len(fake_bot.sent_messages) == 1  # not 2


async def test_no_reminder_when_earnings_not_today(db_session, sample_user, fake_bot):
    watchlist_repo = WatchlistRepository(db_session)
    await watchlist_repo.add(sample_user.id, "AAPL")
    await db_session.commit()

    future_date = (dt.date.today() + dt.timedelta(days=5)).isoformat()

    with patch.object(
        job_mod.market_data, "get_earnings_calendar",
        new=AsyncMock(return_value=[{"symbol": "AAPL", "date": future_date, "hour": "bmo", "eps_estimate": None}]),
    ), patch("src.jobs.earnings_reminder_job.get_session", side_effect=_session_patch(db_session)):
        await job_mod.run_earnings_reminder_check(fake_bot)

    assert fake_bot.sent_messages == []


async def test_only_onboarded_users_are_checked(db_session, fake_bot):
    """
    Regression test for the bug caught during manual testing: get_or_create
    does NOT set onboarding_completed=True by default, so a user who never
    finished onboarding should be silently skipped, not errored on.
    """
    from src.db.repositories.user_repository import UserRepository

    user_repo = UserRepository(db_session)
    user, _ = await user_repo.get_or_create(telegram_id=200002, username="notonboarded", first_name="NotDone")
    # deliberately NOT calling mark_onboarding_step — user.onboarding_completed stays False

    watchlist_repo = WatchlistRepository(db_session)
    await watchlist_repo.add(user.id, "AAPL")
    await db_session.commit()

    today = dt.date.today().isoformat()

    with patch.object(
        job_mod.market_data, "get_earnings_calendar",
        new=AsyncMock(return_value=[{"symbol": "AAPL", "date": today, "hour": "amc", "eps_estimate": 2.35}]),
    ), patch("src.jobs.earnings_reminder_job.get_session", side_effect=_session_patch(db_session)):
        await job_mod.run_earnings_reminder_check(fake_bot)

    assert fake_bot.sent_messages == []  # skipped, not sent, since onboarding never completed
