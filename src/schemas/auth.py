from typing import Annotated, Optional

from fastapi import Form
from pydantic import BaseModel


class AuthData(BaseModel):
    """Модель входных данных при авторизации."""

    login: str
    password: str

    @classmethod
    def as_form(
        cls,
        username: Annotated[Optional[str], Form()] = None,
        login: Annotated[Optional[str], Form()] = None,
        password: Annotated[str, Form(...)] = None,
    ) -> 'AuthData':
        """Создаёт объект AuthData из данных формы."""
        user_login = login or username
        if not user_login:
            raise ValueError('login/username is required')
        return cls(login=user_login, password=password)


class AuthToken(BaseModel):
    """Модель ответа при успешной авторизации."""

    access_token: str
    token_type: str = 'bearer'
