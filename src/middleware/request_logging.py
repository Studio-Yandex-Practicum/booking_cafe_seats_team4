from __future__ import annotations

import logging
import time
import uuid
from typing import Callable, Optional

from sqlalchemy.orm.exc import DetachedInstanceError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from core.logging import get_logger, get_user_logger
from core.reqctx import reset_ctx, set_ctx


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Логирует каждый HTTP-запрос/ответ в единый лог проекта."""

    def __init__(self, app: ASGIApp, logger_name: str = 'api') -> None:
        """Инициализирует middleware.

        Args:
            app: ASGI-приложение.
            logger_name: имя базового логгера для сообщений без user-контекста.

        """
        super().__init__(app)
        self._base_logger = get_logger(logger_name)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Обрабатывает запрос, логируя запрос/ответ и время выполнения.

        Формирует/проставляет X-Request-ID, пишет access-лог (info на успех,
        exception на ошибку) и возвращает ответ.
        """
        req_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        request.state.request_id = req_id

        user = getattr(request.state, 'user', None)
        tokens = set_ctx(req_id, user)

        ip = request.client.host if request.client else '-'
        ua = request.headers.get('user-agent', '-')
        method = request.method
        path = request.url.path

        started = time.perf_counter()

        try:
            response: Response = await call_next(request)
            status = response.status_code
        except Exception as exc:
            logger = self._logger_with_user(request)
            status_for_log = getattr(exc, 'status_code', 500)
            duration_ms = int((time.perf_counter() - started) * 1000)
            msg = (
                f'HTTP {method} {path} -> {status_for_log} '
                f'[{duration_ms}ms; req_id={req_id}; ip={ip}; ua={ua}]'
            )
            logger.exception(msg)
            raise
        finally:
            reset_ctx(tokens)

        duration_ms = int((time.perf_counter() - started) * 1000)
        logger = self._logger_with_user(request)
        msg = (
            f'HTTP {method} {path} -> {status} '
            f'[{duration_ms}ms; req_id={req_id}; ip={ip}; ua={ua}]'
        )
        logger.info(msg)

        response.headers.setdefault('X-Request-ID', req_id)
        return response

    def _logger_with_user(self, request: Request) -> logging.Logger:
        """Возвращает логгер с user-контекстом, если он есть в state."""
        user: Optional[object] = (
            getattr(request.state, 'user', None)
            or getattr(request.state, 'current_user', None)
            or getattr(request.state, 'actor', None)
        )
        if not user:
            return self._base_logger
        try:
            return get_user_logger('api', user)
        except DetachedInstanceError:
            return self._base_logger
        except Exception:
            return self._base_logger
