from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WatchlistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    note: str | None
    added_at: dt.datetime


class WatchlistAddRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=16)
    note: str | None = Field(default=None, max_length=255)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()
