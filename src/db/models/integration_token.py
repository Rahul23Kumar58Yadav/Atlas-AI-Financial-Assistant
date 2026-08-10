from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class IntegrationToken(Base):
    """
    OAuth credentials for a connected third-party account (Gmail, Calendar,
    Drive, Sheets — all share Google OAuth so `provider` distinguishes which
    scope set was granted, in case a user connects them separately).

    Shape matches what google.oauth2.credentials.Credentials needs to
    reconstruct — see services/integrations/google/*_client.py's
    from_token_dict(), which this model's as_token_dict() feeds directly.

    Tokens are stored as plain text here for MVP simplicity. Encrypt
    access_token/refresh_token at rest (e.g. via Fernet) before this
    goes anywhere near production.
    """

    __tablename__ = "integration_tokens"
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_integration_user_provider"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    provider: Mapped[str] = mapped_column(String(32))  # "google" (unified Gmail+Calendar+Drive+Sheets grant, see api/routes/oauth.py)

    access_token: Mapped[str] = mapped_column(String(2048))
    refresh_token: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scopes: Mapped[list] = mapped_column(JSON, default=list)
    token_expiry: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow
    )

    def as_token_dict(self) -> dict:
        """Shape expected by google.oauth2.credentials.Credentials(**this)."""
        return {
            "token": self.access_token,
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scopes": self.scopes,
        }
