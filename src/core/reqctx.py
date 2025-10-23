from __future__ import annotations

from contextvars import ContextVar
from typing import Any, Tuple

_request_id: ContextVar[str | None] = ContextVar(
    'request_id',
    default=None,
)
_user: ContextVar[Any | None] = ContextVar('user', default=None)


def set_ctx(request_id: str | None, user: Any | None) -> Tuple:
    """Установить значения в контекст.

    Сохраняет `request_id` и `user` в ContextVar и возвращает токены,
    которые нужно передать в `reset_ctx()` для восстановления прежних
    значений.
    """
    t1 = _request_id.set(request_id)
    t2 = _user.set(user)
    return t1, t2


def reset_ctx(tokens: Tuple) -> None:
    """Сбросить контекст к прежним значениям.

    Принимает кортеж токенов, полученных из `set_ctx()`, и откатывает
    соответствующие ContextVar.
    """
    t1, t2 = tokens
    _request_id.reset(t1)
    _user.reset(t2)


def get_request_id() -> str | None:
    """Вернуть текущий `request_id` из контекста или `None`."""
    return _request_id.get()


def get_user() -> Any | None:
    """Вернуть текущего пользователя из контекста или `None`."""
    return _user.get()
