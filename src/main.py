from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api import api_router
from core.config import settings
from core.logging import get_logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Инициализация и корректное завершение сервиса."""
    setup_logging()
    log = get_logger(__name__)
    try:
        tail = settings.DATABASE_URL.split('@')[-1]
    except Exception:
        tail = '<unparsed>'
    log.info(f'db_url_tail={tail}')
    log.info('service started')
    try:
        yield
    finally:
        log.info('service shutdown')


app = FastAPI(title='Booking Cafe API', lifespan=lifespan)
"""Основное приложение FastAPI."""


@app.get('/', tags=['health'])
def root() -> dict[str, str]:
    """Проверка доступности сервиса."""
    return {'status': 'ok'}


app.include_router(api_router)
"""Подключение всех маршрутов API."""

if __name__ == '__main__':
    import uvicorn

    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
