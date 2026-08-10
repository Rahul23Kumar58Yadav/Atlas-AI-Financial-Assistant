from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class Document(Base):
    """
    An uploaded document and its extracted text (see services/document_service.py
    for extraction). Storing full extracted_text directly is fine at
    hackathon scale — a real RAG pipeline would instead chunk this into a
    separate embeddings table and keep this row as metadata only.
    """

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(16))  # "pdf" | "txt" | "md" | ...
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_failed: Mapped[bool] = mapped_column(default=False)

    uploaded_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
