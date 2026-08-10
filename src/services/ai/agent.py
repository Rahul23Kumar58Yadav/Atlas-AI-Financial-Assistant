"""
The "brain" of the assistant — classifies intent, decides whether to ask
a clarifying question first, and orchestrates the right response. This is
the same responsibility as core/orchestrator.py; it lives here under
services/ai/ so all AI-facing logic (LLM calls, prompts, agent behavior)
sits in one place, with bot/ only ever calling this one function.
"""
from __future__ import annotations

from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.logging import get_logger
from src.db.models.user import User
from src.services.ai.llm_client import LLMClient
from src.services.ai.memory.long_term import LongTermMemory
from src.services.ai.memory.short_term import ConversationMemory
from src.services.ai.prompts.system_prompt import CLARIFY_SYSTEM_PROMPT, CLASSIFIER_SYSTEM_PROMPT
from src.services.ai.tools import registry

logger = get_logger(__name__)
llm = LLMClient()


class Intent(str, Enum):
    RESEARCH = "research"
    DOCUMENT = "document"
    SCHEDULING = "scheduling"
    PREFERENCE_UPDATE = "preference_update"
    SMALLTALK = "smalltalk"
    AMBIGUOUS = "ambiguous"


async def classify_intent(message: str) -> Intent:
    response = await llm.complete(
        system=CLASSIFIER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": message}],
        max_tokens=10,
    )
    raw = response.text.strip().lower()
    try:
        return Intent(raw)
    except ValueError:
        return Intent.AMBIGUOUS


async def needs_clarification(message: str) -> tuple[bool, str | None]:
    response = await llm.complete(
        system=CLARIFY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": message}],
        max_tokens=100,
    )

    clarify, question = False, None
    for line in response.text.strip().splitlines():
        if line.upper().startswith("CLARIFY:"):
            clarify = "yes" in line.lower()
        elif line.upper().startswith("QUESTION:"):
            question = line.split(":", 1)[1].strip() or None

    return clarify, question if clarify else None


async def run_agent(session: AsyncSession, user: User, text: str) -> str:
    """The single entrypoint bot handlers call — see bot/handlers/text.py etc."""
    conversation_memory = ConversationMemory(session)
    long_term_memory = LongTermMemory(session)

    history = await conversation_memory.get_history_for_llm(user.id)
    user_context = await long_term_memory.get_context_for_user(user.id)

    intent = await classify_intent(text)
    logger.info("intent_classified", user_id=user.id, intent=intent.value)

    if intent == Intent.AMBIGUOUS:
        should_clarify, question = await needs_clarification(text)
        if should_clarify and question:
            await conversation_memory.record_turn(user.id, text, question, intent=intent.value)
            return question

    reply = await _delegate(intent, text, history, user_context, user_id=user.id)

    await conversation_memory.record_turn(user.id, text, reply, intent=intent.value)
    return reply


async def _delegate(intent: Intent, text: str, history: list[dict], user_context: str, user_id: int) -> str:
    from src.services.ai.prompts.system_prompt import RESEARCH_SYSTEM_PROMPT

    if intent in (Intent.RESEARCH, Intent.AMBIGUOUS):
        messages = [*history, {"role": "user", "content": text}]
        return await llm.complete_with_tool_loop(
            system=RESEARCH_SYSTEM_PROMPT.format(user_context=user_context),
            messages=messages,
            tools=registry.RESEARCH_SCHEMAS,
            tool_executor=registry.dispatch,
        )

    if intent == Intent.SMALLTALK:
        return "Hey! What can I help you look into today?"

    if intent == Intent.PREFERENCE_UPDATE:
        return (
            "Got it — I'll start tracking that for you. "
            "(This intent covers both watchlist adds and alert requests; wire it to "
            "services/personalization_service.py for plain watchlist adds, or services/alert_service.py "
            "when a threshold/condition is mentioned — needs real extraction logic to tell them apart, "
            "similar to services/personalization/onboarding.py's _extract().)"
        )

    if intent == Intent.SCHEDULING:
        return await registry.dispatch("manage_calendar_event", {"title": text, "when": "unspecified"})

    if intent == Intent.DOCUMENT:
        return await registry.dispatch("query_document", {"question": text, "user_id": user_id})

    messages = [*history, {"role": "user", "content": text}]
    return await llm.complete_with_tool_loop(
        system=RESEARCH_SYSTEM_PROMPT.format(user_context=user_context),
        messages=messages,
        tools=registry.RESEARCH_SCHEMAS,
        tool_executor=registry.dispatch,
    )
