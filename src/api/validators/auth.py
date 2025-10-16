from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import verify_password
from models.user import User


async def authenticate_user(
    session: AsyncSession,
    login: str,
    password: str,
) -> User:
    """Найти пользователя по email/phone и проверить пароль и активность."""
    login = login.strip()

    stmt = (
        select(User)
        .where((User.email == login) | (User.phone == login))
        .limit(1)
    )
    user = await session.scalar(stmt)

    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Неверный логин или пароль',
    )

    if user is None:
        raise invalid

    if not verify_password(password, user.password_hash):
        raise invalid

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Пользователь неактивен',
        )

    return user
