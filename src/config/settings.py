"""
Centralized application settings.

Everything in the app reads config from here — nothing reads os.environ
directly outside this module. Makes it trivial to see the full surface
area of what's configurable, and to override in tests.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Telegram ---
    telegram_bot_token: str

    # --- AI ---
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-6"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    ai_provider: str = "groq"  # "groq" | "gemini" | "anthropic"

    # --- Market data providers ---
    finnhub_api_key: str | None = None
    sec_edgar_user_agent: str = "AtlasFinancialAssistant contact@example.com"  # SEC requires an identifying UA

    # --- Google OAuth (Gmail/Calendar/Drive/Sheets) ---
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_oauth_redirect_uri: str = "http://localhost:8000/oauth/google/callback"

    # --- Database ---
    database_url: str = "sqlite+aiosqlite:///./atlas.db"

    # --- API server ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # --- Scheduler defaults (used until a user sets their own preference) ---
    default_briefing_hour: int = 8
    default_briefing_minute: int = 0
    default_timezone: str = "UTC"

    # --- Logging / environment ---
    log_level: str = "INFO"
    environment: str = "development"

    # --- Feature flags ---
    feature_voice_enabled: bool = True
    feature_image_enabled: bool = True
    feature_daily_briefing_enabled: bool = True
    feature_alerts_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    """Settings are read once and cached — restart the process to pick up .env changes."""
    return Settings()