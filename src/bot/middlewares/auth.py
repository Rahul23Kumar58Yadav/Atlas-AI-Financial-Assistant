"""
Resolves the Telegram user to an internal User row, creating one on first
contact. Injects `user` and `session` into handler data so handlers never
touch the DB session lifecycle themselves.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from src.db.base import get_session
from src.db.repositories.user_repository import UserRepository


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        telegram_user = data.get("event_from_user")
        if telegram_user is None:
            return await handler(event, data)

        async with get_session() as session:
            repo = UserRepository(session)
            user, created = await repo.get_or_create(
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
            )
            data["session"] = session
            data["user"] = user
            data["is_new_user"] = created
            return await handler(event, data)
