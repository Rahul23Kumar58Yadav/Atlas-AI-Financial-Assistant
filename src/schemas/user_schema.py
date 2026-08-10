"""
Pydantic schemas for User. Keeps API request/response shapes decoupled
from the SQLAlchemy model — UserResponse deliberately excludes internal
fields (onboarding_step) that callers of an external API shouldn't see.
"""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # lets .model_validate(orm_instance) work directly

    id: int
    telegram_id: int
    telegram_username: str | None
    first_name: str | None
    role: str | None
    onboarding_completed: bool
    created_at: dt.datetime


class UserUpdateRequest(BaseModel):
    """For an internal/admin endpoint to correct a user's role, etc. — not user-facing."""

    role: str | None = None
