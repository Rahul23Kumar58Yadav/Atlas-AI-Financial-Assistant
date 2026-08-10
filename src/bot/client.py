from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from src.config.settings import get_settings

settings = get_settings()


def create_bot() -> Bot:
    # Plain text by default — avoids MarkdownV2 escaping edge cases on LLM output.
    # If you want rich formatting, switch to HTML parse mode and have the LLM
    # emit <b>/<i> tags instead, which is far less fragile than MarkdownV2.
    return Bot(token=settings.telegram_bot_token)


def create_dispatcher() -> Dispatcher:
    return Dispatcher(storage=MemoryStorage())
