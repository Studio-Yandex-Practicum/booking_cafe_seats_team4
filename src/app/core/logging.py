import logging
import sys
from logging import Logger, LoggerAdapter
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Tuple

from app.core.config import settings


class SafeExtraFormatter(logging.Formatter):
    """Перед форматированием гарантирует поля user и user_id."""

    def format(self, record: logging.LogRecord) -> str:
        """Гарантирует user/user_id и вызывает базовый форматтер."""
        if not hasattr(record, 'user'):
            record.user = 'SYSTEM'
        if not hasattr(record, 'user_id'):
            record.user_id = 'SYSTEM'
        return super().format(record)


class UserAdapter(LoggerAdapter):
    """Адаптер: добавляет user-контекст к логам."""

    def process(self, msg: Any, kwargs: Dict) -> Tuple[Any, Dict]:
        """Объединить extra адаптера с extra из вызова."""
        extra = {**self.extra, **kwargs.get('extra', {})}
        kwargs['extra'] = extra
        return msg, kwargs


def setup_logging() -> None:
    """Инициализировать базовую конфигурацию логирования."""
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # создаём хендлеры вручную
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if settings.LOG_FILE:
        file_handler = RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=1_000_000,
            backupCount=3,
            encoding='utf-8',
        )
        handlers.append(file_handler)

    fmt = (
        '%(asctime)s | %(levelname)s | %(name)s | '
        'user=%(user)s id=%(user_id)s | %(message)s'
    )
    formatter = SafeExtraFormatter(fmt)

    for h in handlers:
        h.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    for h in handlers:
        root.addHandler(h)


def get_logger(name: str) -> Logger:
    """Получить обычный логгер без user-контекста."""
    return logging.getLogger(name)


def get_user_logger(name: str, user: Any | None) -> LoggerAdapter:
    """Получить логгер с user-контекстом (username/id)."""
    username = getattr(user, 'username', 'SYSTEM')
    user_id = getattr(user, 'id', 'SYSTEM')
    base = logging.getLogger(name)
    return UserAdapter(base, {'user': username, 'user_id': user_id})
