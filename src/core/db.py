from collections.abc import AsyncIterator

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

Base = declarative_base()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Возвращает асинхронную сессию БД для зависимостей FastAPI."""
    async with AsyncSessionLocal() as session:
        logger.info('Сессия открыта')
        try:
            yield session
        except (HTTPException, StarletteHTTPException) as e:
            await session.rollback()
            logger.info('HTTP исключение в сессии, откатываем: %s', e.detail)
            raise
        except Exception:
            await session.rollback()
            logger.exception('Ошибка в сессии, откатываем')
            raise
        finally:
            logger.info('Сессия закрыта.')


__all__ = ['engine', 'AsyncSessionLocal', 'get_session']
