from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import settings

_pwd_ctx = CryptContext(schemes=['bcrypt_sha256'], deprecated='auto')


def hash_password(password: str) -> str:
    """Вернуть хэш для заданного пароля (bcrypt_sha256)."""
    return _pwd_ctx.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Проверить соответствие пароля его хэшу (bcrypt_sha256)."""
    return _pwd_ctx.verify(plain_password, password_hash)


def create_access_token(
    subject: str,
    expires_in_minutes: Optional[int] = None,
) -> str:
    """Создать JWT с sub=<subject> и TTL (мин)."""
    ttl = (
        expires_in_minutes
        if expires_in_minutes is not None
        else settings.TOKEN_IDLE_TTL_MIN
    )
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        'sub': subject,
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(minutes=ttl)).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET, algorithm=settings.JWT_ALGO)


class TokenError(JWTError):
    """Общий класс ошибок токена для унификации обработки."""


def decode_token(token: str) -> dict[str, Any]:
    """Декодировать JWT и вернуть payload."""
    try:
        return jwt.decode(
            token,
            settings.SECRET,
            algorithms=[settings.JWT_ALGO],
        )
    except JWTError as exc:
        raise TokenError(str(exc)) from exc
