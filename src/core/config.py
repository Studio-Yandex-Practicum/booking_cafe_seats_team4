import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_ROOT = PROJECT_ROOT / '.env'
ENV_INFRA = PROJECT_ROOT / 'infra' / '.env'

load_dotenv(ENV_ROOT, override=False)
load_dotenv(ENV_INFRA, override=False)


@dataclass(frozen=True)
class Settings:
    """Настройки проекта."""

    # JWT
    SECRET: str = os.getenv('SECRET', 'CHANGE_ME_SUPER_SECRET_32CHARS_MIN')
    JWT_ALGO: str = os.getenv('JWT_ALGO', 'HS256')
    TOKEN_IDLE_TTL_MIN: int = int(os.getenv('TOKEN_IDLE_TTL_MIN', '30'))

    # DB
    DATABASE_URL: str = (
        os.getenv('DATABASE_URL')
        or 'postgresql+asyncpg://'
        f'{os.getenv("POSTGRES_USER", "")}:'
        f'{os.getenv("POSTGRES_PASSWORD", "")}'
        f'@{os.getenv("POSTGRES_SERVER", "localhost")}:'
        f'{os.getenv("POSTGRES_PORT", "5432")}/'
        f'{os.getenv("POSTGRES_DB", "")}'
    )

    # Media
    MEDIA_PATH: Path = Path(os.getenv('MEDIA_PATH', '/media'))

    # Celery & RabbitMQ
    CELERY_BROKER_URL: str = os.getenv(
        'CELERY_BROKER_URL',
        'amqp://guest:guest@localhost:5672/',
    )
    CELERY_RESULT_BACKEND: str = os.getenv(
        'CELERY_RESULT_BACKEND',
        'redis://localhost:6379/0',
    )

    # SMTP
    SMTP_HOST: str = os.getenv('SMTP_HOST', 'smtp.yandex.ru')
    SMTP_PORT: int = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME: str = os.getenv(
        'SMTP_USERNAME',
        'python-plus-53-54-cafe@yandex.ru'
    )
    SMTP_PASSWORD: str = os.getenv('SMTP_PASSWORD', 'jlezoiiqptbwgmae')

    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str | None = os.getenv('LOG_FILE')


settings = Settings()
"""Экземпляр настроек для использования в проекте."""
