from __future__ import annotations

from aiogram import Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.formatters.telegram_markdown import format_for_telegram
from src.core.orchestrator import handle_message
from src.db.models.user import User
from src.services.ai.transcription import transcribe_voice_note

router = Router(name="voice")


@router.message(lambda m: m.voice is not None)
async def handle_voice_message(message: Message, user: User, session: AsyncSession):
    file = await message.bot.get_file(message.voice.file_id)
    audio_bytes = await message.bot.download_file(file.file_path)

    text = await transcribe_voice_note(audio_bytes.read())
    if not text.strip():
        await message.answer("I couldn't make out that voice note — could you try again or type it out?")
        return

    reply = await handle_message(session, user, text)
    for chunk in format_for_telegram(reply):
        await message.answer(chunk)
