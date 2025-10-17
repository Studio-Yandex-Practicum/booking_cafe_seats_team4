from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.exceptions import forbidden, unauthorized
from core.security import verify_password
from models.user import User


async def authenticate_user(
    session: AsyncSession,
    login: str,
    password: str,
) -> User:
    """Найти пользователя по email/phone."""
    login = login.strip()

    stmt = (
        select(User)
        .where((User.email == login) | (User.phone == login))
        .limit(1)
    )
    user = await session.scalar(stmt)

    if user is None:
        raise unauthorized('Неверный логин или пароль')

    if not verify_password(password, user.password_hash):
        raise unauthorized('Неверный логин или пароль')

    if not user.is_active:
        raise forbidden('Пользователь неактивен')

    return user
