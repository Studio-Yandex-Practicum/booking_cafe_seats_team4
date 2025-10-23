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


def _attach_req_id(request: Request, response: JSONResponse) -> JSONResponse:
    """Добавляет X-Request-ID из request.state к ответу (если есть)."""
    rid = getattr(request.state, 'request_id', None)
    if rid:
        response.headers['X-Request-ID'] = rid
    return response


def _format_json_response(
    request: Request,
    status_code: int,
    detail: object,
) -> JSONResponse:
    """Формирует JSON-ответ по тем же правилам, что и раньше."""
    if isinstance(detail, dict) and 'code' in detail and 'message' in detail:
        content = detail
    else:
        if isinstance(detail, str):
            message = detail
        else:
            message = DEFAULT_MESSAGES.get(int(status_code), 'Ошибка')
        content = {'code': int(status_code), 'message': message}
    return _attach_req_id(
        request,
        JSONResponse(status_code=status_code, content=content),
    )


async def http_exc_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Обработать StarletteHTTPException и вернуть унифицированный JSON."""
    return _format_json_response(request, int(exc.status_code), exc.detail)


async def http_exc_fastapi_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Обработать fastapi.HTTPException и вернуть унифицированный JSON."""
    return _format_json_response(request, int(exc.status_code), exc.detail)


async def pydantic_exc_handler(
    request: Request,
    __: RequestValidationError,
) -> JSONResponse:
    """Вернуть 422 для ошибок валидации с фиксированным сообщением."""
    return _attach_req_id(
        request,
        JSONResponse(
            status_code=422,
            content={'code': 422, 'message': 'Неверные данные запроса'},
        ),
    )


async def integrity_exc_handler(
    request: Request,
    exc: IntegrityError,
) -> JSONResponse:
    """Преобразует IntegrityError в 400; для unique/duplicate."""
    txt = str(exc).lower()
    if ('unique' in txt) or ('duplicate' in txt):
        return _attach_req_id(
            request,
            JSONResponse(
                status_code=400,
                content={'code': 400, 'message': DUPLICATE_MSG},
            ),
        )
    return _attach_req_id(
        request,
        JSONResponse(
            status_code=400,
            content={
                'code': 400,
                'message': 'Нарушение ограничений базы данных',
            },
        ),
    )


async def unhandled_exc_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Перехватить прочие исключения и вернуть статус/JSON в едином формате."""
    status_code = getattr(exc, 'status_code', 500)
    detail = getattr(exc, 'detail', None)
    return _format_json_response(request, int(status_code), detail)


def install(app: FastAPI) -> None:
    """Зарегистрировать глобальные обработчики на приложении."""
    app.add_exception_handler(
        StarletteHTTPException,
        http_exc_handler,
    )
    app.add_exception_handler(
        HTTPException,
        http_exc_fastapi_handler,
    )
    app.add_exception_handler(
        RequestValidationError,
        pydantic_exc_handler,
    )
    app.add_exception_handler(
        IntegrityError,
        integrity_exc_handler,
    )
    app.add_exception_handler(
        Exception,
        unhandled_exc_handler,
    )
