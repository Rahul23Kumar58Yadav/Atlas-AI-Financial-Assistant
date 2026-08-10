from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.watchlist import WatchlistItem


class WatchlistRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_id: int, symbol: str, note: str | None = None) -> WatchlistItem:
        symbol = symbol.upper()
        existing = await self.get_one(user_id, symbol)
        if existing:
            return existing

        item = WatchlistItem(user_id=user_id, symbol=symbol, note=note)
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_one(self, user_id: int, symbol: str) -> WatchlistItem | None:
        result = await self.session.execute(
            select(WatchlistItem).where(WatchlistItem.user_id == user_id, WatchlistItem.symbol == symbol.upper())
        )
        return result.scalar_one_or_none()

    async def get_symbols_for_user(self, user_id: int) -> list[str]:
        result = await self.session.execute(select(WatchlistItem).where(WatchlistItem.user_id == user_id))
        return [item.symbol for item in result.scalars().all()]

    async def remove(self, user_id: int, symbol: str) -> None:
        item = await self.get_one(user_id, symbol)
        if item:
            await self.session.delete(item)
