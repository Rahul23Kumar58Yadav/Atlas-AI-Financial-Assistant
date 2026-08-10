from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class Preference(Base):
    """
    One row per user. `followed_sectors`/`insight_types` stay as JSON lists
    for MVP simplicity — the watchlist used to live here too as JSON, but
    is now its own table (see db/models/watchlist.py) so alert/briefing
    queries can join against it directly instead of deserializing JSON.
    """

    __tablename__ = "preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

    followed_sectors: Mapped[list] = mapped_column(JSON, default=list)    # e.g. ["semiconductors", "AI"]
    insight_types: Mapped[list] = mapped_column(JSON, default=list)       # e.g. ["earnings", "filings"]

    briefing_hour: Mapped[int] = mapped_column(Integer, default=8)
    briefing_minute: Mapped[int] = mapped_column(Integer, default=0)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")

    user = relationship("User", back_populates="preference")
