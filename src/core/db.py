from collections.abc import AsyncIterator
from http import HTTPStatus
from fastapi import HTTPException
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import settings
from src.core.logging import get_logger


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
            await session.commit()
            logger.info('Изменения в бд зафиксированы.')
        except Exception as err:
            logger.error(f'Ошибка в сессии: {err}')
            await session.rollback()
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=str(err)
            )
        finally:
            logger.info('Сессия закрыта.')


__all__ = ['engine', 'AsyncSessionLocal', 'get_session']
