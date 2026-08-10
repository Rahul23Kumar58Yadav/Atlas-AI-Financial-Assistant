"""
Shared fixtures. Every test gets a fresh in-memory SQLite DB (fast, fully
isolated — no shared state or cleanup needed between tests) rather than
hitting the same file-based DB used in manual/dev runs.
"""
from __future__ import annotations

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.db.base import Base
from src.db.repositories.user_repository import UserRepository


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    # Import models so they register on Base.metadata before create_all — same
    # requirement as src.db.base.init_db, but scoped to an in-memory engine here.
    from src.db.models import (  # noqa: F401
        alert_rule,
        conversation,
        document,
        integration_token,
        memory_fact,
        preference,
        user,
        watchlist,
    )

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def sample_user(db_session: AsyncSession):
    """A pre-onboarded user — most tests don't care about the onboarding state machine itself."""
    user_repo = UserRepository(db_session)
    user, _created = await user_repo.get_or_create(telegram_id=100001, username="testuser", first_name="Test")
    await user_repo.mark_onboarding_step(user, step="done", completed=True)
    await db_session.flush()
    return user


class FakeBot:
    """Drop-in replacement for aiogram.Bot in tests — records sent messages instead of calling Telegram."""

    def __init__(self):
        self.sent_messages: list[tuple[int, str]] = []

    async def send_message(self, chat_id: int, text: str, **kwargs):
        self.sent_messages.append((chat_id, text))


@pytest_asyncio.fixture
def fake_bot() -> FakeBot:
    return FakeBot()
