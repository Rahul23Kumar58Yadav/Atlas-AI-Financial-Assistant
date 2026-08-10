from __future__ import annotations

from aiogram import Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.formatters.telegram_markdown import format_for_telegram
from src.core.orchestrator import handle_message
from src.db.models.user import User
from src.services.ai.vision import describe_image

router = Router(name="image")


@router.message(lambda m: m.photo is not None)
async def handle_image_message(message: Message, user: User, session: AsyncSession):
    largest_photo = message.photo[-1]
    file = await message.bot.get_file(largest_photo.file_id)
    image_bytes = await message.bot.download_file(file.file_path)

    caption = message.caption or "The user sent this image without a caption — describe it and ask what they want."
    description = await describe_image(image_bytes.read(), caption)

    reply = await handle_message(session, user, f"[Image attached] {caption}\n\nImage contents: {description}")
    for chunk in format_for_telegram(reply):
        await message.answer(chunk)
