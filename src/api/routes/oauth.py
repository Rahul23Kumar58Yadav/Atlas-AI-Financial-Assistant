"""
Google OAuth flow for connecting Gmail/Calendar/Drive/Sheets. Two endpoints:
  GET /oauth/google/authorize?telegram_id=...  -> redirects the user's
      browser to Google's consent screen
  GET /oauth/google/callback                    -> Google redirects back
      here with a code; we exchange it for tokens and persist them

Requires GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / GOOGLE_OAUTH_REDIRECT_URI
in .env, and that redirect URI registered in Google Cloud Console.

Security note: `state` here is just the telegram_id, which is enough to
route the callback to the right user but is NOT a CSRF-safe opaque token.
For anything beyond local/hackathon use, generate a signed, single-use
state value and verify it here instead.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db_session
from src.config.logging import get_logger
from src.config.settings import get_settings
from src.db.repositories.integration_repository import IntegrationRepository
from src.db.repositories.user_repository import UserRepository

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter(prefix="/oauth/google", tags=["oauth"])

# One combined scope set covering all four Google integrations — a single
# consent screen, one token, reused by GmailClient/CalendarClient/DriveClient/
# SheetsClient. Split into per-service flows if you want users to grant them separately.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]

PROVIDER_KEY = "google"  # single row in IntegrationToken covers all four scopes/clients


def _build_flow() -> Flow:
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth isn't configured — set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env",
        )

    client_config = {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_oauth_redirect_uri],
        }
    }
    return Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=settings.google_oauth_redirect_uri)


@router.get("/authorize")
async def authorize(telegram_id: int = Query(..., description="The Telegram user connecting their Google account")):
    flow = _build_flow()
    authorization_url, _state = flow.authorization_url(
        access_type="offline",       # request a refresh_token, not just a short-lived access token
        include_granted_scopes="true",
        prompt="consent",
        state=str(telegram_id),
    )
    return RedirectResponse(authorization_url)


@router.get("/callback")
async def callback(
    code: str = Query(...),
    state: str = Query(...),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        telegram_id = int(state)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found — did they start a conversation with the bot first?")

    flow = _build_flow()
    try:
        flow.fetch_token(code=code)
    except Exception as exc:  # noqa: BLE001 — surface as a clean 400 rather than a raw OAuth library traceback
        logger.error("google_oauth_token_exchange_failed", telegram_id=telegram_id, error=str(exc))
        raise HTTPException(status_code=400, detail="Failed to exchange authorization code for tokens")

    credentials = flow.credentials

    integration_repo = IntegrationRepository(session)
    await integration_repo.upsert(
        user_id=user.id,
        provider=PROVIDER_KEY,
        access_token=credentials.token,
        refresh_token=credentials.refresh_token,
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=list(credentials.scopes or SCOPES),
    )

    logger.info("google_oauth_connected", telegram_id=telegram_id, user_id=user.id)

    return {"status": "connected", "message": "Google account connected — you can close this tab and return to the chat."}
