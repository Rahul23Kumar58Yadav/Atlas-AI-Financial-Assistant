from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class WatchlistItem(Base):
    """
    One row per (user, ticker). Replaces the JSON list that used to live on
    Preference — normalized so each entry can carry its own metadata
    (when it was added, an optional note) without the blob growing
    unbounded, and so alert/briefing queries can join against it directly
    instead of deserializing JSON in Python.
    """

    __tablename__ = "watchlist_items"
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_watchlist_user_symbol"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    symbol: Mapped[str] = mapped_column(String(16), index=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)  # e.g. "watching for earnings"

    added_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
