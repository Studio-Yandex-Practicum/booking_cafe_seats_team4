import logging
import sys
from logging import Logger, LoggerAdapter
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Tuple

from src.core.config import settings
from src.core.constants import (
    DEFAULT_USER_ID,
    DEFAULT_USER_NAME,
    LOG_BACKUP_COUNT,
    LOG_FORMAT,
    LOG_MAX_BYTES,
)


class SafeExtraFormatter(logging.Formatter):
    """Перед форматированием проверяет поля user и user_id."""

    def format(self, record: logging.LogRecord) -> str:
        """Проверяет user и форматирует запись."""
        if not hasattr(record, 'user'):
            record.user = DEFAULT_USER_NAME
        if not hasattr(record, 'user_id'):
            record.user_id = DEFAULT_USER_ID
        return super().format(record)


class UserAdapter(LoggerAdapter):
    """Адаптер: добавляет user-контекст к логам."""

    def process(self, msg: Any, kwargs: Dict) -> Tuple[Any, Dict]:
        """Добавляет контекст пользователя в extra."""
        extra = {**self.extra, **kwargs.get('extra', {})}
        kwargs['extra'] = extra
        return msg, kwargs


def setup_logging() -> None:
    """Инициализирвем базовый конфиг логирования."""
    level_name = getattr(settings, 'LOG_LEVEL', 'INFO')
    level = getattr(logging, level_name.upper(), logging.INFO)

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    log_file = getattr(settings, 'LOG_FILE', None)
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8',
        )
        handlers.append(file_handler)

    formatter = SafeExtraFormatter(LOG_FORMAT)
    for h in handlers:
        h.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    for h in handlers:
        root.addHandler(h)


def get_logger(name: str) -> Logger:
    """Получаем обычный логгер без user-контекста."""
    return logging.getLogger(name)


def get_user_logger(name: str, user: Any | None) -> LoggerAdapter:
    """Получаем логгер с user-контекстом (username/id)."""
    username = getattr(user, 'username', DEFAULT_USER_NAME)
    user_id = getattr(user, 'id', DEFAULT_USER_ID)
    base = logging.getLogger(name)
    return UserAdapter(base, {'user': username, 'user_id': user_id})
