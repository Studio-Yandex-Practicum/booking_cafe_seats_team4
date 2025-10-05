from fastapi import FastAPI

from src.api import api_router
from src.core.config import settings
from src.core.logging import get_logger, setup_logging

app = FastAPI(title='Booking Cafe API')
"""Основное приложение FastAPI."""


@app.on_event('startup')
async def _startup() -> None:
    """Инициализация при запуске приложения."""
    setup_logging()
    log = get_logger(__name__)
    try:
        tail = settings.DATABASE_URL.split('@')[-1]
    except Exception:
        tail = '<unparsed>'
    log.info(f'db_url_tail={tail}')
    log.info('service started')


@app.get('/', tags=['health'])
def root() -> dict[str, str]:
    """Проверка доступности сервиса."""
    return {'status': 'ok'}


app.include_router(api_router)
"""Подключение всех маршрутов API."""


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        'src.main:app',
        host='0.0.0.0',
        port=8000,
        reload=True,
    )
