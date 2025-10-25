from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.validators.users import \
    apply_user_update as apply_user_update  # noqa: F401
from core.security import hash_password
from models.user import User
from schemas.user import UserRole

__all__ = ['apply_user_update', 'ensure_superuser']


async def ensure_superuser(
    session: AsyncSession,
    login: str,
    password: str,
    username: Optional[str] = None,
) -> User:
    """Найдёт или создаст ADMIN-пользователя. Идемпотентно.

    login — email ИЛИ телефон (один из).
    """
    login = (login or '').strip()
    if not login:
        raise ValueError('login должен быть email или телефоном')
    if not password:
        raise ValueError('password не должен быть пустым')

    user = await session.scalar(
        select(User)
        .where((User.email == login) | (User.phone == login))
        .limit(1),
    )

    if user:
        changed = False
        if getattr(user, 'role', None) != int(UserRole.ADMIN):
            user.role = int(UserRole.ADMIN)
            changed = True
        if not getattr(user, 'is_active', True):
            user.is_active = True
            changed = True
        if changed:
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user

    if '@' in login:
        email, phone = login, None
    else:
        email, phone = None, login

    if not (email or phone):
        raise ValueError('login должен быть email или телефоном')

    new_user = User(
        username=(username or 'admin'),
        email=email,
        phone=phone,
        role=int(UserRole.ADMIN),
        is_active=True,
        password_hash=hash_password(password),
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


if __name__ == '__main__':
    import asyncio
    import getpass
    import os
    import sys

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from core.config import settings

    login = os.getenv('SU_LOGIN') or input('Login (email/phone): ').strip()
    password = os.getenv('SU_PASSWORD') or getpass.getpass('Password: ')
    username = os.getenv('SU_USERNAME') or 'admin'

    if not login or not password:
        print(
            'Usage:\n  SU_LOGIN=<email|phone> SU_PASSWORD=<pass> '
            'python -m services.users\n'
            'или просто запустите без ENV и введите значения вручную.',
        )
        sys.exit(2)

    if sys.platform.startswith('win'):
        try:
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy(),
            )
        except Exception:
            pass

    async def _run() -> None:
        engine = create_async_engine(settings.DATABASE_URL, future=True)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as s:
            u = await ensure_superuser(
                s,
                login=login,
                password=password,
                username=username,
            )
            print(
                f'OK: superuser id={u.id}, login={login}, '
                f'active={u.is_active}, role={u.role}',
            )
        await engine.dispose()

    asyncio.run(_run())
