"""
Voice note -> text. Thin wrapper around STTClient
(services/integrations/voice/stt_client.py) — kept as a single function
here so bot/handlers/voice.py doesn't need to know which provider or
client class is used underneath.
"""
from __future__ import annotations

from src.config.logging import get_logger
from src.services.integrations.voice.stt_client import STTClient

logger = get_logger(__name__)
_stt_client = STTClient()


async def transcribe_voice_note(audio_bytes: bytes) -> str:
    return await _stt_client.transcribe(audio_bytes)
