"""
App entrypoint. Runs the Telegram bot (long polling), the FastAPI server
(for health checks / future OAuth callbacks), and the APScheduler jobs
all inside one asyncio event loop — simplest possible deployment for an
MVP/hackathon. Split into separate processes later if you need to scale
each independently.
"""
from __future__ import annotations

import asyncio

import uvicorn

from src.api.app import app as fastapi_app
from src.bot.client import create_bot, create_dispatcher
from src.bot.router import register_routers
from src.config.logging import configure_logging, get_logger
from src.config.settings import get_settings
from src.db.base import init_db
from src.jobs.scheduler import create_scheduler

logger = get_logger(__name__)


async def run_bot() -> None:
    bot = create_bot()
    dp = create_dispatcher()
    register_routers(dp)

    scheduler = create_scheduler(bot)
    scheduler.start()

    logger.info("bot_starting")
    await dp.start_polling(bot)


async def run_api() -> None:
    settings = get_settings()
    config = uvicorn.Config(fastapi_app, host=settings.api_host, port=settings.api_port, log_level="info")
    server = uvicorn.Server(config)
    logger.info("api_starting", host=settings.api_host, port=settings.api_port)
    await server.serve()


async def main() -> None:
    configure_logging()
    logger.info("atlas_starting")

    await init_db()
    logger.info("db_initialized")

    await asyncio.gather(run_bot(), run_api())


if __name__ == "__main__":
    asyncio.run(main())
