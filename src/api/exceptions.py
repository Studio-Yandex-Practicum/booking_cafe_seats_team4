from __future__ import annotations

from typing import Final

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

DEFAULT_MESSAGES: Final[dict[int, str]] = {
    400: 'Некорректный запрос',
    401: 'Требуется авторизация',
    403: 'Недостаточно прав',
    404: 'Не найдено',
    422: 'Неверные данные запроса',
}

DUPLICATE_MSG: Final[str] = (
    'Пользователь с таким email или телефоном уже существует'
)


def err(code: int, message: str, status: int) -> HTTPException:
    """HTTPException с detail={'code': int, 'message': str}."""
    return HTTPException(
        status_code=status,
        detail={'code': code, 'message': message},
    )


def bad_request(message: str) -> HTTPException:
    """400 Bad Request."""
    return err(400, message, 400)


def unauthorized(message: str) -> HTTPException:
    """401 Unauthorized."""
    return err(401, message, 401)


def forbidden(message: str) -> HTTPException:
    """403 Forbidden."""
    return err(403, message, 403)


def not_found(message: str) -> HTTPException:
    """404 Not Found."""
    return err(404, message, 404)


def unprocessable(message: str) -> HTTPException:
    """422 Unprocessable Entity."""
    return err(422, message, 422)


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

        message = DEFAULT_MESSAGES.get(exc.status_code, 'Ошибка')
        if isinstance(exc.detail, str):
            message = exc.detail

        return JSONResponse(
            status_code=exc.status_code,
            content={'code': int(exc.status_code), 'message': message},
        )

    @app.exception_handler(RequestValidationError)
    async def pydantic_exc(
        _: Request,
        __: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={'code': 422, 'message': 'Неверные данные запроса'},
        )

    @app.exception_handler(IntegrityError)
    async def integrity_exc(
        _: Request,
        exc: IntegrityError,
    ) -> JSONResponse:
        txt = str(exc).lower()
        if ('unique' in txt) or ('duplicate' in txt):
            return JSONResponse(
                status_code=400,
                content={'code': 400, 'message': DUPLICATE_MSG},
            )
        return JSONResponse(
            status_code=400,
            content={
                'code': 400,
                'message': 'Нарушение ограничений базы данных',
            },
        )
