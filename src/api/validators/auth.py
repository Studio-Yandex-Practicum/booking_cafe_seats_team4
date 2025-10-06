from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import verify_password
from src.models.user import User


async def authenticate_user(
    session: AsyncSession,
    login: str,
    password: str,
) -> User:
    """Найти пользователя, проверить пароль."""
    stmt = (
        select(User)
        .where((User.email == login) | (User.phone == login))
        .limit(1)
    )
    user = await session.scalar(stmt)

    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid credentials',
    )

    if not user:
        raise invalid

    if not verify_password(password, user.password_hash):
        raise invalid

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Inactive user',
        )

    return user
