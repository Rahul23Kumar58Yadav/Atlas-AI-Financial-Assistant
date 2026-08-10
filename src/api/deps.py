"""
FastAPI dependency-injection helpers. Two concerns:
  1. Handing routes a DB session via Depends(), instead of every route
     opening `async with get_session()` itself (see watchlist.py for the
     pre-refactor version of that duplication).
  2. Resolving telegram_id (a URL path param) into an actual User row
     once, so routes don't each repeat the "get_by_telegram_id or 404" check.
"""
from __future__ import annotations

from typing import AsyncIterator

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.base import AsyncSessionLocal
from src.db.models.user import User
from src.db.repositories.user_repository import UserRepository


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """
    FastAPI-flavored session dependency. Deliberately separate from
    db.base.get_session (used elsewhere) because that one commits/rolls
    back as a context manager for service-layer code; FastAPI's Depends
    wants a plain async generator instead. Commits on success, rolls back
    on any exception raised inside the route.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(telegram_id: int, session: AsyncSession) -> User:
    """
    Resolves a URL path param (telegram_id) into an actual User row, or
    raises 404. Not itself a Depends()-decorated dependency — it needs two
    independently resolved values (the path param and the session), which
    FastAPI's Depends() can't compose directly. Routes call it explicitly:

        async def route(telegram_id: int, session: AsyncSession = Depends(get_db_session)):
            user = await get_current_user(telegram_id, session)
    """
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
