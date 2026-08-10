"""
Google Sheets client. Backs "summarize this spreadsheet" / "detect
anomalies in my model" style requests — reads ranges as plain values,
letting the AI layer do the actual analysis.
"""
from __future__ import annotations

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.config.logging import get_logger

logger = get_logger(__name__)


class SheetsClient:
    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self._service = build("sheets", "v4", credentials=credentials, cache_discovery=False)

    @classmethod
    def from_token_dict(cls, token_data: dict) -> "SheetsClient":
        return cls(Credentials(**token_data))

    def read_range(self, spreadsheet_id: str, range_name: str) -> list[list[str]]:
        """`range_name` e.g. 'Sheet1!A1:F50'. Returns raw rows of string/number values."""
        try:
            result = self._service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range_name
            ).execute()
        except Exception as exc:  # noqa: BLE001
            logger.error("sheets_read_failed", spreadsheet_id=spreadsheet_id, error=str(exc))
            return []

        return result.get("values", [])

    def list_sheet_titles(self, spreadsheet_id: str) -> list[str]:
        """Useful before read_range, to know what tabs exist in a workbook."""
        try:
            result = self._service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        except Exception as exc:  # noqa: BLE001
            logger.error("sheets_metadata_failed", spreadsheet_id=spreadsheet_id, error=str(exc))
            return []

        return [sheet["properties"]["title"] for sheet in result.get("sheets", [])]
