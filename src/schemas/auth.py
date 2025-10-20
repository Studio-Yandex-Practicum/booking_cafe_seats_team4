from typing import Annotated

from fastapi import Form
from pydantic import BaseModel, Field


class AuthData(BaseModel):
    """Входные данные при авторизации (форма: login + password)."""

    login: str = Field(..., description='Email или телефон')
    password: str = Field(..., description='Пароль')

    @classmethod
    def as_form(
        cls,
        login: Annotated[str, Form(..., description='Email или телефон')],
        password: Annotated[str, Form(..., description='Пароль')],
    ) -> 'AuthData':
        """Собирает модель из полей HTML-формы (login, password)."""
        return cls(login=login, password=password)


class AuthToken(BaseModel):
    """Ответ при успешной авторизации."""

    access_token: str
    token_type: str = 'bearer'
