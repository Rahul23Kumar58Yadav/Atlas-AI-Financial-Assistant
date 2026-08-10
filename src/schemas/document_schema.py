from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    """
    Deliberately excludes `extracted_text` — full document text has no
    business being in a list/metadata response; use DocumentDetailResponse
    when the caller actually needs the content.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_type: str
    extraction_failed: bool
    uploaded_at: dt.datetime


class DocumentDetailResponse(DocumentResponse):
    extracted_text: str | None


class DocumentQuestionRequest(BaseModel):
    question: str
