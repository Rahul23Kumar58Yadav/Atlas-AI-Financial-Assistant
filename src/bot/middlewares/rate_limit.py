"""
Per-user message rate limiting. Referenced in the original architecture
doc but never implemented until now — uses utils/rate_limiter.py so the
windowing logic isn't duplicated here.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from src.utils.rate_limiter import RateLimiter

# 10 messages per 30 seconds — generous enough for normal conversation,
# tight enough to stop a runaway script or accidental double-send loop.
_limiter = RateLimiter(max_requests=10, window_seconds=30)


class RateLimitMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        telegram_user = data.get("event_from_user")
        key = str(telegram_user.id) if telegram_user else "anonymous"

        if not _limiter.is_allowed(key):
            wait_seconds = _limiter.seconds_until_next_slot(key)
            await event.answer(f"Slow down a little — try again in about {wait_seconds:.0f}s.")
            return None

        return await handler(event, data)
