"""
Schemas for a hypothetical /chat HTTP endpoint — useful if you ever want
to hit the same orchestrator (services/ai/agent.py) from something other
than Telegram (a web demo, internal testing tool, etc.) without duplicating
validation logic.
"""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    telegram_id: int = Field(..., description="Identifies the user; same identity as in Telegram")
    text: str = Field(..., min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str
    intent: str | None = None


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    intent: str | None
    created_at: dt.datetime
