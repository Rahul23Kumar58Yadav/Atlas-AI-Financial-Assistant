"""
Decides when the assistant should ask a follow-up question instead of
guessing. This is the module behind the brief's example: "Tell me about
Apple" should prompt "news, earnings, valuation, or overview?" rather than
returning a generic wall of text.

Kept separate from intent_router so the reasoning ("is this specific enough
to act on") is explicit and testable on its own.
"""
from __future__ import annotations

from src.services.ai.llm_client import LLMClient

llm = LLMClient()

CLARIFY_SYSTEM_PROMPT = """You help a financial assistant decide whether a user's request is specific \
enough to answer directly, or vague enough that a quick follow-up question would produce a much better \
answer.

Respond in this exact format, nothing else:
CLARIFY: yes|no
QUESTION: <a single, short, natural follow-up question — only if CLARIFY is yes, else leave blank>

Ask for clarification when the request names a company/topic but not what aspect the user wants \
(e.g. "tell me about Apple" — news? earnings? valuation? overview?), or when a comparison/analysis \
request doesn't specify criteria. Do NOT ask for clarification when the request is already specific \
(e.g. "what's Apple's stock price", "summarize Apple's latest earnings call in 5 points").
"""


async def needs_clarification(message: str) -> tuple[bool, str | None]:
    response = await llm.complete(
        system=CLARIFY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": message}],
        max_tokens=100,
    )

    clarify = False
    question = None
    for line in response.text.strip().splitlines():
        if line.upper().startswith("CLARIFY:"):
            clarify = "yes" in line.lower()
        elif line.upper().startswith("QUESTION:"):
            question = line.split(":", 1)[1].strip() or None

    return clarify, question if clarify else None
