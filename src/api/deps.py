from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, Response, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from core.security import TokenError, decode_token
from models.user import User
from schemas.user import UserRole

bearer_scheme = HTTPBearer(auto_error=False)
bearer_optional = HTTPBearer(auto_error=False)


async def get_current_user(
    _: Response,
    creds: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Security(bearer_scheme),
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Возвращает текущего пользователя по Bearer-токену."""
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not authenticated',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    token = creds.credentials
    try:
        payload = decode_token(token)
    except TokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    sub = payload.get('sub')
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='User not found',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Inactive user',
        )
    return user


async def get_current_user_optional(
    session: Annotated[AsyncSession, Depends(get_session)],
    creds: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Security(bearer_optional),
    ] = None,
) -> Optional[User]:
    """Вернёт активного пользователя или None (без 401/403)."""
    if not creds or not creds.credentials:
        return None

    token = creds.credentials
    try:
        payload = decode_token(token)
    except TokenError:
        return None

    sub = payload.get('sub')
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        return None

    user = await session.get(User, user_id)
    if not user or not user.is_active:
        return None
    return user


async def inject_user_into_state(
    request: Request,
    user: Annotated[Optional[User], Depends(get_current_user_optional)],
) -> None:
    """Кладёт пользователя (если есть) в request.state.user."""
    request.state.user = user


async def require_manager_or_admin(
    current: Annotated[User, Depends(get_current_user)],
) -> User:
    """Проверяет, что текущий пользователь - менеджер или админ."""
    if current.role not in (int(UserRole.MANAGER), int(UserRole.ADMIN)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Forbidden',
        )
    return current
