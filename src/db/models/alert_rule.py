from __future__ import annotations

import datetime as dt

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class AlertRule(Base):
    """
    A standing alert a user asked for, e.g. "notify me if TSLA moves more
    than 5% in a day". `condition_type` + `threshold` are intentionally
    narrow (percent-move only) for the MVP — extend condition_type to
    support "sec_filing", "news_keyword", etc. as separate evaluators in
    jobs/alert_check_job.py without changing this schema much.
    """

    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    symbol: Mapped[str] = mapped_column(String(16), index=True)
    condition_type: Mapped[str] = mapped_column(String(32), default="percent_move")  # percent_move | sec_filing
    threshold_percent: Mapped[float | None] = mapped_column(Float, nullable=True)  # e.g. 5.0 for "moves >5%"

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_triggered_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
