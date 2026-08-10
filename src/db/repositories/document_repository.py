from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.document import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, user_id: int, filename: str, file_type: str, extracted_text: str | None, extraction_failed: bool = False
    ) -> Document:
        document = Document(
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            extracted_text=extracted_text,
            extraction_failed=extraction_failed,
        )
        self.session.add(document)
        await self.session.flush()
        return document

    async def get_most_recent(self, user_id: int) -> Document | None:
        """Used to resolve "this document" when the user asks a follow-up without re-uploading."""
        result = await self.session.execute(
            select(Document).where(Document.user_id == user_id).order_by(desc(Document.uploaded_at)).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, document_id: int) -> Document | None:
        return await self.session.get(Document, document_id)

    async def get_recent_for_user(self, user_id: int, limit: int = 10) -> list[Document]:
        result = await self.session.execute(
            select(Document).where(Document.user_id == user_id).order_by(desc(Document.uploaded_at)).limit(limit)
        )
        return list(result.scalars().all())
