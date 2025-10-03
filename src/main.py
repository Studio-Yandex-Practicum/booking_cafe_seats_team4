"""Запускает базовое логирование и пишет тестовую строку в лог.

Проверка, что всё собрано и работает.
"""

from core.logging import get_logger, setup_logging


def main() -> None:
    """Инициализировать логирование и записать тестовый лог."""
    setup_logging()
    log = get_logger(__name__)
    log.info('service started')


if __name__ == '__main__':
    main()
