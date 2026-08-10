"""
Gmail client. Takes Google OAuth credentials for a specific user (obtained
via whatever OAuth flow handles the consent screen — not built yet, see
README) and wraps the handful of calls the assistant actually needs:
searching messages and reading thread content for context/summarization.
"""
from __future__ import annotations

import base64

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.config.logging import get_logger

logger = get_logger(__name__)


class GmailClient:
    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self._service = build("gmail", "v1", credentials=credentials, cache_discovery=False)

    @classmethod
    def from_token_dict(cls, token_data: dict) -> "GmailClient":
        """
        `token_data` is whatever was persisted after OAuth consent, e.g.
        {"token": ..., "refresh_token": ..., "client_id": ..., "client_secret": ..., "scopes": [...]}
        """
        return cls(Credentials(**token_data))

    def search_messages(self, query: str, max_results: int = 10) -> list[dict]:
        """
        `query` uses Gmail's normal search syntax, e.g. 'from:ir@company.com subject:earnings'.
        Returns lightweight metadata; call get_message_body for full content.
        """
        try:
            result = self._service.users().messages().list(
                userId="me", q=query, maxResults=max_results
            ).execute()
        except Exception as exc:  # noqa: BLE001 — surface as empty results, let the agent explain
            logger.error("gmail_search_failed", error=str(exc))
            return []

        return result.get("messages", [])

    def get_message_body(self, message_id: str) -> str:
        try:
            message = self._service.users().messages().get(
                userId="me", id=message_id, format="full"
            ).execute()
        except Exception as exc:  # noqa: BLE001
            logger.error("gmail_get_message_failed", message_id=message_id, error=str(exc))
            return ""

        return self._extract_plain_text(message.get("payload", {}))

    def _extract_plain_text(self, payload: dict) -> str:
        """Gmail messages are MIME multipart — walk parts looking for text/plain."""
        if payload.get("mimeType") == "text/plain" and "data" in payload.get("body", {}):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

        for part in payload.get("parts", []):
            text = self._extract_plain_text(part)
            if text:
                return text
        return ""
