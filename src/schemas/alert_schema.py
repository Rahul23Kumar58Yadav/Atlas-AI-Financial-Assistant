from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    condition_type: str
    threshold_percent: float | None
    is_active: bool
    last_triggered_at: dt.datetime | None
    created_at: dt.datetime


class AlertCreateRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=16)
    threshold_percent: float = Field(..., gt=0, le=100, description="e.g. 5.0 for 'moves more than 5%'")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()
