from __future__ import annotations

import os
import sys
import asyncio
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Alembic base config
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# PYTHONPATH
CURR = Path(__file__).resolve()
SRC_ROOT = CURR.parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# Project imports
from core.config import settings
from models.base import Base  # noqa: E402
import models

target_metadata = Base.metadata

# DB URL
alembic_url = os.getenv("ALEMBIC_DATABASE_URL", settings.DATABASE_URL)
config.set_main_option("sqlalchemy.url", alembic_url)


# Offline
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (генерация SQL без подключения)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# Online
def do_run_migrations(connection: Connection) -> None:
    """Configure context and run migrations in a single transaction."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create async engine, open connection and run migrations."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# Entrypoint
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
