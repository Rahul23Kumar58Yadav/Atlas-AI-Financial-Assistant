"""
Lightweight intent classification. Deliberately simple (one small LLM call,
plain enum out) — this isn't meant to be a big NLU system, just enough to
route to the right agent and to let clarification.py reason about ambiguity.
"""
from __future__ import annotations

from enum import Enum

from src.services.ai.llm_client import LLMClient

llm = LLMClient()


class Intent(str, Enum):
    RESEARCH = "research"              # company/market lookups, news, comparisons
    DOCUMENT = "document"               # questions about an uploaded file
    SCHEDULING = "scheduling"            # reminders, meetings, calendar actions
    PREFERENCE_UPDATE = "preference_update"  # "track TSLA for me", "brief me at 7am"
    SMALLTALK = "smalltalk"              # greetings, thanks, chit-chat
    AMBIGUOUS = "ambiguous"              # not enough info to route confidently


CLASSIFIER_SYSTEM_PROMPT = """You classify a user's message into exactly one intent for a financial \
assistant. Respond with only the single lowercase intent word, nothing else.

Intents:
- research: asking about a company, market, comparison, or financial topic
- document: referring to a document they uploaded or want analyzed
- scheduling: reminders, meetings, calendar-related requests
- preference_update: asking to track/watch something or change notification settings
- smalltalk: greetings, thanks, casual chat
- ambiguous: too vague to act on without a follow-up question (e.g. "tell me about Apple" \
with no specifics about what aspect)
"""


async def classify_intent(message: str, has_recent_document: bool = False) -> Intent:
    context_note = (
        "\nNote: the user has an uploaded document in recent context."
        if has_recent_document
        else ""
    )
    response = await llm.complete(
        system=CLASSIFIER_SYSTEM_PROMPT + context_note,
        messages=[{"role": "user", "content": message}],
        max_tokens=10,
    )
    raw = response.text.strip().lower()
    try:
        return Intent(raw)
    except ValueError:
        return Intent.AMBIGUOUS
