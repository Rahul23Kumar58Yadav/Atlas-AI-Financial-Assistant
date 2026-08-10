"""
Speech-to-text client, wrapping OpenAI's Whisper API. Isolated here as
the one integrations client that isn't Google or market-data related —
voice notes need transcription before they can go through the same
text pipeline as everything else.
"""
from __future__ import annotations

import io

from openai import AsyncOpenAI

from src.config.logging import get_logger

logger = get_logger(__name__)


class STTClient:
    def __init__(self, model: str = "whisper-1"):
        self.model = model
        self._client: AsyncOpenAI | None = None  # created lazily — see _get_client

    def _get_client(self) -> AsyncOpenAI:
        """
        Lazy init: constructing AsyncOpenAI() eagerly raises if OPENAI_API_KEY
        isn't set, which would crash the whole app at import time even for
        users who never enable voice. Only fail when transcription is actually used.
        """
        if self._client is None:
            self._client = AsyncOpenAI()
        return self._client

    async def transcribe(self, audio_bytes: bytes, filename: str = "voice.ogg") -> str:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename

        try:
            client = self._get_client()
            transcript = await client.audio.transcriptions.create(model=self.model, file=audio_file)
            return transcript.text
        except Exception as exc:  # noqa: BLE001 — transcription failures shouldn't crash the bot
            logger.error("stt_transcription_failed", error=str(exc))
            return ""
