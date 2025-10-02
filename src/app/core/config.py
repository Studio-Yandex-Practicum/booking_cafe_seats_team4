import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Настройки приложения, читаемые из env-переменных."""

    # JWT
    SECRET: str = os.getenv('SECRET', 'CHANGE_ME_SUPER_SECRET_32CHARS_MIN')
    JWT_ALGO: str = os.getenv('JWT_ALGO', 'HS256')
    TOKEN_IDLE_TTL_MIN: int = int(os.getenv('TOKEN_IDLE_TTL_MIN', '30'))

    # logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str | None = os.getenv('LOG_FILE')


settings = Settings()
