"""
Registers all handlers and middleware on the Dispatcher. This file contains
no business logic — just wiring, in a fixed order:
  1. middlewares (auth first, so every handler gets `user`/`session`)
  2. handlers, most specific first (voice/image/document before catch-all text)
"""
from __future__ import annotations

from aiogram import Dispatcher

from src.bot.handlers import document, image, text, voice
from src.bot.middlewares.auth import AuthMiddleware
from src.bot.middlewares.rate_limit import RateLimitMiddleware
from src.bot.middlewares.typing_indicator import TypingIndicatorMiddleware


def register_routers(dp: Dispatcher) -> None:
    dp.message.middleware(RateLimitMiddleware())  # reject before auth touches the DB
    dp.message.middleware(AuthMiddleware())
    dp.message.middleware(TypingIndicatorMiddleware())

    dp.include_router(voice.router)
    dp.include_router(image.router)
    dp.include_router(document.router)
    dp.include_router(text.router)  # catch-all — must be last
