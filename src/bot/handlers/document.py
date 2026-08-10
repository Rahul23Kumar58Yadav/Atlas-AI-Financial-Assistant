from __future__ import annotations

from aiogram import Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.logging import get_logger
from src.db.models.user import User
from src.db.repositories.document_repository import DocumentRepository
from src.services.document_service import document_service

logger = get_logger(__name__)
router = Router(name="document")


@router.message(lambda m: m.document is not None)
async def handle_document_message(message: Message, user: User, session: AsyncSession):
    file_name = message.document.file_name or "document"
    file_type = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "unknown"

    file = await message.bot.get_file(message.document.file_id)
    file_bytes = await message.bot.download_file(file.file_path)

    extracted_text = document_service.extract_text(file_bytes.read(), file_name)
    extraction_failed = not extracted_text.strip()

    doc_repo = DocumentRepository(session)
    await doc_repo.create(
        user_id=user.id,
        filename=file_name,
        file_type=file_type,
        extracted_text=extracted_text if not extraction_failed else None,
        extraction_failed=extraction_failed,
    )

    if extraction_failed:
        await message.answer(
            f"I couldn't extract readable text from {file_name} — it may be a scanned image or "
            "an unsupported format. Supported: PDF, TXT, MD."
        )
        return

    logger.info("document_ingested", user_id=user.id, filename=file_name, char_count=len(extracted_text))

    summary = await document_service.summarize(extracted_text)
    await message.answer(f"Got {file_name} — here's the gist:\n\n{summary}\n\nAsk me anything else about it.")
