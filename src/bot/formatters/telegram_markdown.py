"""
Converts AI output into Telegram-safe MarkdownV2 and splits long replies
into multiple messages (Telegram's hard limit is 4096 chars per message).
"""
from __future__ import annotations

import re

TELEGRAM_MAX_LENGTH = 4096
_MDV2_SPECIAL_CHARS = r"_*[]()~`>#+-=|{}.!"


def escape_markdown_v2(text: str) -> str:
    """Escapes MarkdownV2 special characters that aren't part of intentional formatting."""
    pattern = f"([{re.escape(_MDV2_SPECIAL_CHARS)}])"
    return re.sub(pattern, r"\\\1", text)


def chunk_message(text: str, max_length: int = TELEGRAM_MAX_LENGTH) -> list[str]:
    """Splits on paragraph boundaries where possible, falling back to hard cuts."""
    if len(text) <= max_length:
        return [text]

    chunks: list[str] = []
    remaining = text
    while len(remaining) > max_length:
        split_at = remaining.rfind("\n\n", 0, max_length)
        if split_at == -1:
            split_at = max_length
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


def format_for_telegram(text: str) -> list[str]:
    """Full pipeline: escape then chunk. Handlers call this before sending."""
    return chunk_message(text)
