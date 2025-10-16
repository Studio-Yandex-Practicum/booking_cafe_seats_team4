from collections.abc import AsyncIterator
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.declarative import declarative_base

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
            # Коммит убираем отсюда. Коммитить нужно в CRUD-слое,
            # где происходит изменение данных. Зависимость не должна
            # неявно коммитить всё подряд.
            # await session.commit()
        except HTTPException as e:
            # Если это HTTPException, его нужно просто пробросить дальше.
            # Не логируем его как ошибку,
            # т.к. это ожидаемое поведение (404, 403 и т.д.).
            # На всякий случай, если были изменения до ошибки
            await session.rollback()
            logger.info(f'HTTP исключение в сессии, откатываем: {e.detail}')
            raise e
        except Exception as err:
            logger.error(f'Ошибка в сессии: {err}', exc_info=True)
            await session.rollback()
            # Можно выбросить свою кастомную 500 ошибку или стандартную
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail='Internal Server Error',
            )
        finally:
            logger.info('Сессия закрыта.')


__all__ = ['engine', 'AsyncSessionLocal', 'get_session']
