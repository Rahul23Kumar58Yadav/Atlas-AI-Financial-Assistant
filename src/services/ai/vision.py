"""
Image -> text description, using Claude's native vision support (no
separate provider needed, unlike transcription).
"""
from __future__ import annotations

import base64

from anthropic import AsyncAnthropic

from src.config.settings import get_settings

settings = get_settings()
_client = AsyncAnthropic(api_key=settings.anthropic_api_key)


async def describe_image(image_bytes: bytes, caption: str) -> str:
    """
    Describes an image (chart screenshot, filing excerpt, slide, etc.) in
    terms useful for a financial assistant — the caller feeds the result
    into the orchestrator as extra context, not as the final answer.
    """
    encoded = base64.b64encode(image_bytes).decode("utf-8")

    response = await _client.messages.create(
        model=settings.anthropic_model,
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/jpeg", "data": encoded},
                    },
                    {
                        "type": "text",
                        "text": (
                            f"Caption from user: '{caption}'. Describe what's in this image, focusing on "
                            "any financial data, charts, tickers, numbers, or text that's relevant to a "
                            "finance professional. Be factual and concise."
                        ),
                    },
                ],
            }
        ],
    )
    return "\n".join(block.text for block in response.content if block.type == "text")
