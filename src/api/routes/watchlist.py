"""
Watchlist endpoints. Refactored to use api/deps.py's get_db_session +
get_current_user instead of each route opening its own session and
repeating the "get_by_telegram_id or 404" check.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_db_session
from src.db.models.watchlist import WatchlistItem
from src.db.repositories.watchlist_repository import WatchlistRepository
from src.schemas.watchlist_schema import WatchlistAddRequest, WatchlistItemResponse

router = APIRouter(prefix="/users/{telegram_id}/watchlist", tags=["watchlist"])


@router.get("", response_model=list[WatchlistItemResponse])
async def list_watchlist(telegram_id: int, session: AsyncSession = Depends(get_db_session)):
    user = await get_current_user(telegram_id, session)

    result = await session.execute(select(WatchlistItem).where(WatchlistItem.user_id == user.id))
    items = result.scalars().all()
    return [WatchlistItemResponse.model_validate(item) for item in items]


@router.post("", response_model=WatchlistItemResponse, status_code=201)
async def add_to_watchlist(
    telegram_id: int, body: WatchlistAddRequest, session: AsyncSession = Depends(get_db_session)
):
    user = await get_current_user(telegram_id, session)

    watchlist_repo = WatchlistRepository(session)
    item = await watchlist_repo.add(user.id, body.symbol, note=body.note)
    return WatchlistItemResponse.model_validate(item)


@router.delete("/{symbol}", status_code=204)
async def remove_from_watchlist(telegram_id: int, symbol: str, session: AsyncSession = Depends(get_db_session)):
    user = await get_current_user(telegram_id, session)

    watchlist_repo = WatchlistRepository(session)
    await watchlist_repo.remove(user.id, symbol)
