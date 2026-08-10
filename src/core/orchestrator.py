"""
Thin re-export. The actual brain — intent classification, clarification,
and delegation — lives in services/ai/agent.py (kept under services/ai/ so
all AI-facing logic and prompts sit in one place). Bot handlers import
`handle_message` from here so the call site reads naturally as
"orchestrator.handle_message" without caring where the implementation lives.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.user import User
from src.services.ai.agent import run_agent


async def handle_message(session: AsyncSession, user: User, text: str) -> str:
    return await run_agent(session, user, text)
