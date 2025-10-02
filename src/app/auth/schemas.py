from pydantic import BaseModel


class AuthData(BaseModel):
    """Входные данные для логина (username + password)."""

    username: str
    password: str


class AuthToken(BaseModel):
    """Ответ при логине: access token и его тип."""

    access_token: str
    token_type: str
