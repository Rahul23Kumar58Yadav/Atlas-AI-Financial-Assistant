from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class MemoryFact(Base):
    """
    A single extracted long-term fact about a user, e.g.
    key="watches_ticker" value="NVDA" source="conversation:1423"

    Kept separate from Preference so freeform facts (which don't fit a
    fixed schema) can accumulate without migrations.
    """

    __tablename__ = "memory_facts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    key: Mapped[str] = mapped_column(String(128))
    value: Mapped[str] = mapped_column(Text)
    source_message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id"), nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
