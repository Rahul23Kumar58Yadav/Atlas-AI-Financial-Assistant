"""
Registers (or removes) a Telegram webhook, as an alternative to the long
polling main.py uses by default. Useful once you're deploying somewhere
with a public HTTPS URL (Render, Fly.io, etc.) instead of running locally —
webhooks avoid the constant polling overhead and give Telegram push-based
delivery instead.

Note: switching to webhook mode also requires adding a POST route to
api/app.py that calls dp.feed_update(bot, update) — this script only
handles the Telegram-side registration, not the receiving endpoint.

Usage:
    python -m scripts.register_webhook set https://your-domain.com/telegram/webhook
    python -m scripts.register_webhook delete
    python -m scripts.register_webhook info
"""
from __future__ import annotations

import argparse
import asyncio

from aiogram import Bot

from src.config.logging import configure_logging, get_logger
from src.config.settings import get_settings

logger = get_logger(__name__)


async def set_webhook(url: str) -> None:
    settings = get_settings()
    bot = Bot(token=settings.telegram_bot_token)

    try:
        success = await bot.set_webhook(url=url, drop_pending_updates=True)
        logger.info("webhook_set", url=url, success=success)
    finally:
        await bot.session.close()


async def delete_webhook() -> None:
    settings = get_settings()
    bot = Bot(token=settings.telegram_bot_token)

    try:
        success = await bot.delete_webhook(drop_pending_updates=True)
        logger.info("webhook_deleted", success=success)
    finally:
        await bot.session.close()


async def get_webhook_info() -> None:
    settings = get_settings()
    bot = Bot(token=settings.telegram_bot_token)

    try:
        info = await bot.get_webhook_info()
        logger.info(
            "webhook_info",
            url=info.url or "(none — currently in polling mode)",
            pending_update_count=info.pending_update_count,
            last_error_message=info.last_error_message,
        )
    finally:
        await bot.session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the Telegram webhook registration")
    subparsers = parser.add_subparsers(dest="command", required=True)

    set_parser = subparsers.add_parser("set", help="Register a webhook URL")
    set_parser.add_argument("url", help="Public HTTPS URL Telegram should POST updates to")

    subparsers.add_parser("delete", help="Remove the webhook (falls back to polling)")
    subparsers.add_parser("info", help="Show current webhook status")

    args = parser.parse_args()
    configure_logging()

    try:
        if args.command == "set":
            asyncio.run(set_webhook(args.url))
        elif args.command == "delete":
            asyncio.run(delete_webhook())
        elif args.command == "info":
            asyncio.run(get_webhook_info())
    except Exception as exc:  # noqa: BLE001 — this is a CLI tool; a clean message beats a raw traceback
        logger.error("webhook_command_failed", command=args.command, error=str(exc))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
