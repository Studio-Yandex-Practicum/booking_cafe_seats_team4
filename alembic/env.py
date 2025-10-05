from __future__ import annotations

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Базовая настройка
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Корень проекта и PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ENV / DATABASE_URL
load_dotenv(PROJECT_ROOT / 'infra' / '.env')
load_dotenv(PROJECT_ROOT / '.env')
load_dotenv()

database_url = os.getenv('DATABASE_URL')
if not database_url:
    pg_user = os.getenv('POSTGRES_USER', '')
    pg_pass = os.getenv('POSTGRES_PASSWORD', '')
    pg_db = os.getenv('POSTGRES_DB', '')
    pg_host = os.getenv('POSTGRES_SERVER', 'localhost')
    pg_port = os.getenv('POSTGRES_PORT', '5432')
    database_url = (
        f'postgresql+asyncpg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}'
    )

# Побрасываем URL в конфиг Alembic
config.set_main_option('sqlalchemy.url', database_url)

# Модели / metadata
import src.models.cafe  # noqa: F401,E402
import src.models.cafe_manager  # noqa: F401,E402
import src.models.user  # noqa: F401,E402
from src.models.base import Base  # noqa: E402

target_metadata = Base.metadata


# ---------- Offline ----------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )
    with context.begin_transaction():
        context.run_migrations()


# Online
def do_run_migrations(connection: Connection) -> None:
    """Configure context and run migrations in a single transaction."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create async engine, open connection and run migrations."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Запускает онлайн-миграции через asyncio."""
    asyncio.run(run_async_migrations())


# Entrypoint
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
