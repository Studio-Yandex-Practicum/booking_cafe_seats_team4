from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

DUPLICATE_MSG = 'Пользователь с таким email или телефоном уже существует'


def err(code: str, message: str, status: int) -> HTTPException:
    """Сформировать HTTPException в формате {'code','message'}."""
    return HTTPException(
        status_code=status,
        detail={'code': code, 'message': message},
    )


def install(app: FastAPI) -> None:
    """Зарегистрировать глобальные обработчики на приложении."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exc(
        _: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        if (
            isinstance(exc.detail, dict)
            and 'code' in exc.detail
            and 'message' in exc.detail
        ):
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail,
            )

        defaults: dict[int, tuple[str, str]] = {
            400: ('BAD_REQUEST', 'Некорректный запрос'),
            401: ('UNAUTHORIZED', 'Требуется авторизация'),
            403: ('FORBIDDEN', 'Недостаточно прав'),
            404: ('NOT_FOUND', 'Не найдено'),
            422: (
                'UNPROCESSABLE_ENTITY',
                'Неверные данные запроса',
            ),
        }
        code, msg = defaults.get(exc.status_code, ('ERROR', 'Ошибка'))
        if isinstance(exc.detail, str):
            msg = exc.detail

        return JSONResponse(
            status_code=exc.status_code,
            content={'code': code, 'message': msg},
        )

    @app.exception_handler(RequestValidationError)
    async def pydantic_exc(
        _: Request,
        __: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                'code': 'VALIDATION_ERROR',
                'message': 'Неверные данные запроса',
            },
        )

    @app.exception_handler(IntegrityError)
    async def integrity_exc(
        _: Request,
        exc: IntegrityError,
    ) -> JSONResponse:
        text = str(exc).lower()
        if 'unique' in text or 'duplicate' in text:
            return JSONResponse(
                status_code=400,
                content={'code': 'USER_DUPLICATE', 'message': DUPLICATE_MSG},
            )
        return JSONResponse(
            status_code=400,
            content={
                'code': 'DB_CONSTRAINT_VIOLATION',
                'message': 'Нарушение ограничений базы данных',
            },
        )
