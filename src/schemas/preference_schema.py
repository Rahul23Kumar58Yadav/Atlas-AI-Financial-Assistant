from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    followed_sectors: list[str]
    insight_types: list[str]
    briefing_hour: int
    briefing_minute: int
    timezone: str


class PreferenceUpdateRequest(BaseModel):
    """All fields optional — a PATCH-style partial update."""

    followed_sectors: list[str] | None = None
    insight_types: list[str] | None = None
    briefing_hour: int | None = Field(default=None, ge=0, le=23)
    briefing_minute: int | None = Field(default=None, ge=0, le=59)
    timezone: str | None = None
