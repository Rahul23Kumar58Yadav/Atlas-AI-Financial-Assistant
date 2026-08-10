"""
Google Calendar client. Backs the scheduling agent / calendar_tool once
OAuth is wired up — creating events (meetings, earnings-call reminders)
and listing upcoming events for meeting prep.
"""
from __future__ import annotations

import datetime as dt

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.config.logging import get_logger

logger = get_logger(__name__)


class CalendarClient:
    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self._service = build("calendar", "v3", credentials=credentials, cache_discovery=False)

    @classmethod
    def from_token_dict(cls, token_data: dict) -> "CalendarClient":
        return cls(Credentials(**token_data))

    def create_event(
        self,
        title: str,
        start: dt.datetime,
        end: dt.datetime,
        description: str = "",
        calendar_id: str = "primary",
    ) -> dict | None:
        event_body = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start.isoformat()},
            "end": {"dateTime": end.isoformat()},
        }
        try:
            return self._service.events().insert(calendarId=calendar_id, body=event_body).execute()
        except Exception as exc:  # noqa: BLE001
            logger.error("calendar_create_event_failed", title=title, error=str(exc))
            return None

    def list_upcoming_events(self, max_results: int = 10, calendar_id: str = "primary") -> list[dict]:
        now = dt.datetime.utcnow().isoformat() + "Z"
        try:
            result = self._service.events().list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
        except Exception as exc:  # noqa: BLE001
            logger.error("calendar_list_events_failed", error=str(exc))
            return []

        return result.get("items", [])
