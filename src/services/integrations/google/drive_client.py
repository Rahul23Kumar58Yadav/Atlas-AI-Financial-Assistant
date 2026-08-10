"""
Google Drive client. Used for finding and pulling financial documents
(reports, decks) the user has stored in Drive rather than uploading
directly to Telegram.
"""
from __future__ import annotations

import io

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from src.config.logging import get_logger

logger = get_logger(__name__)


class DriveClient:
    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self._service = build("drive", "v3", credentials=credentials, cache_discovery=False)

    @classmethod
    def from_token_dict(cls, token_data: dict) -> "DriveClient":
        return cls(Credentials(**token_data))

    def search_files(self, query: str, max_results: int = 10) -> list[dict]:
        """
        `query` uses Drive's search syntax, e.g. "name contains 'Q3 earnings'".
        Returns [{"id", "name", "mimeType", "modifiedTime"}, ...].
        """
        try:
            result = self._service.files().list(
                q=query,
                pageSize=max_results,
                fields="files(id, name, mimeType, modifiedTime)",
            ).execute()
        except Exception as exc:  # noqa: BLE001
            logger.error("drive_search_failed", error=str(exc))
            return []

        return result.get("files", [])

    def download_file(self, file_id: str) -> bytes:
        try:
            request = self._service.files().get_media(fileId=file_id)
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            done = False
            while not done:
                _status, done = downloader.next_chunk()
            return buffer.getvalue()
        except Exception as exc:  # noqa: BLE001
            logger.error("drive_download_failed", file_id=file_id, error=str(exc))
            return b""
