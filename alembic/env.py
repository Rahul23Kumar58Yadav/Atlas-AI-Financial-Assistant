"""
Alembic environment, rewritten for async SQLAlchemy. The default
`alembic init` template assumes a sync engine — that doesn't work with
aiosqlite/asyncpg, so both offline and online migration paths here use
`run_sync()` inside an async engine instead of the generated boilerplate.

Reads DATABASE_URL from our own settings (src/config/settings.py) rather
than alembic.ini's sqlalchemy.url, so there's exactly one place the DB URL
is configured.
"""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from src.config.settings import get_settings
from src.db.base import Base

# Import every model so they register on Base.metadata before Alembic
# compares it against the DB - same requirement as src/db/base.py::init_db.
from src.db.models import (  # noqa: F401,E402
    alert_rule,
    conversation,
    document,
    integration_token,
    memory_fact,
    preference,
    user,
    watchlist,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Override whatever's in alembic.ini with our actual app settings -
# keeps the DB URL defined in exactly one place (.env / settings.py).
config.set_main_option("sqlalchemy.url", get_settings().database_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
