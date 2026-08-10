"""
Async SQLAlchemy engine + session factory, plus the declarative Base
that every model inherits from.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config.settings import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Standard unit-of-work: one session per logical operation, commit or rollback."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create tables if they don't exist. Fine for a hackathon MVP; use Alembic for real migrations."""
    # Import models so they register on Base.metadata before create_all
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

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
