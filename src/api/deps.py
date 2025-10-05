from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_session
from src.core.security import TokenError, decode_token
from src.models.user import User
from src.schemas.user import UserRole

# должно совпадать с POST /auth/login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Раскодировать JWT, достать пользователя и проверить активность."""
    try:
        payload = decode_token(token)
    except TokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token',
        )

    sub = payload.get('sub')
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token',
        )

    user = await session.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='User not found',
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Inactive user',
        )
    return user


def require_manager_or_admin(
    current: Annotated[User, Depends(get_current_user)],
) -> User:
    """Разрешить доступ только MANAGER/ADMIN."""
    if current.role not in (int(UserRole.MANAGER), int(UserRole.ADMIN)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Forbidden',
        )
    return current
