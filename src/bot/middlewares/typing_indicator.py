"""Keeps the "typing…" indicator alive while the orchestrator/LLM call is in flight."""
from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.enums import ChatAction
from aiogram.types import Message, TelegramObject


class TypingIndicatorMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        stop = asyncio.Event()

        async def _keep_typing():
            while not stop.is_set():
                await event.bot.send_chat_action(event.chat.id, ChatAction.TYPING)
                await asyncio.sleep(4)

        task = asyncio.create_task(_keep_typing())
        try:
            return await handler(event, data)
        finally:
            stop.set()
            task.cancel()
