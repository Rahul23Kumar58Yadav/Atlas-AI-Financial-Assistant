from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.formatters.telegram_markdown import format_for_telegram
from src.core.orchestrator import handle_message
from src.db.models.user import User
from src.services.personalization.onboarding import get_next_onboarding_prompt

router = Router(name="text")


@router.message(CommandStart())
async def handle_start(message: Message, user: User, session: AsyncSession, is_new_user: bool):
    """
    No slash-command menu beyond /start (Telegram requires some entrypoint) —
    everything after this is natural conversation, including onboarding.
    """
    if is_new_user or not user.onboarding_completed:
        prompt = await get_next_onboarding_prompt(session, user)
        await message.answer(prompt)
        return

    await message.answer(f"Welcome back{f', {user.first_name}' if user.first_name else ''}. What's on your mind?")


@router.message()
async def handle_text_message(message: Message, user: User, session: AsyncSession):
    if not message.text:
        return

    if not user.onboarding_completed:
        from src.services.personalization.onboarding import process_onboarding_reply

        reply = await process_onboarding_reply(session, user, message.text)
        await message.answer(reply)
        return

    reply = await handle_message(session, user, message.text)
    for chunk in format_for_telegram(reply):
        await message.answer(chunk)
