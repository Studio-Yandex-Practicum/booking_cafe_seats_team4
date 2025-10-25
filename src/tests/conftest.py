from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Generator

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, update
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session as ORMSession

from core.config import settings
from core.db import get_session
from main import app
from models.user import User
from schemas.user import UserRole


@pytest.fixture(scope='session')
def anyio_backend() -> str:
    """Бэкенд для anyio."""
    return 'asyncio'


@pytest.fixture(scope='session', autouse=True)
def _install_savepoint_restart_listener() -> None:
    """Листенер: пересоздать SAVEPOINT после commit()."""

    @event.listens_for(ORMSession, 'after_transaction_end')
    def _restart_savepoint(sess: ORMSession, trans: Any) -> None:
        parent = getattr(trans, '_parent', None)
        if getattr(trans, 'nested', False) and not getattr(
            parent,
            'nested',
            False,
        ):
            sess.begin_nested()


@pytest.fixture()
async def test_engine() -> AsyncIterator[AsyncEngine]:
    """Тестовый движок SQLAlchemy (function scope)."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture()
async def db_conn(
    test_engine: AsyncEngine,
) -> AsyncIterator[AsyncConnection]:
    """Соединение БД + внешняя транзакция + первый SAVEPOINT."""
    async with test_engine.connect() as conn:
        outer_tx = await conn.begin()
        await conn.begin_nested()
        try:
            yield conn
        finally:
            await outer_tx.rollback()


@pytest.fixture()
def sessionmaker(
    db_conn: AsyncConnection,
) -> async_sessionmaker[AsyncSession]:
    """Фабрика AsyncSession, привязанная к соединению теста."""
    return async_sessionmaker(
        bind=db_conn,
        expire_on_commit=False,
        class_=AsyncSession,
    )


@pytest.fixture(autouse=True)
def _override_get_session(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> Generator[None, None, None]:
    """Переопределение зависимости get_session для теста."""

    async def _get_session() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    app.dependency_overrides[get_session] = _get_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
async def client() -> AsyncIterator[AsyncClient]:
    """HTTP-клиент с управлением жизненным циклом приложений."""
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url='http://test',
        ) as c:
            yield c


async def _create_user(
    client: AsyncClient,
    *,
    username: str = 'alice',
    password: str = 'qwe123',
    email: str | None = 'a@a.com',
    phone: str | None = None,
) -> Dict:
    """Создать пользователя через API и вернуть JSON."""
    payload: Dict[str, str] = {'username': username, 'password': password}
    if email is not None:
        payload['email'] = email
    if phone is not None:
        payload['phone'] = phone
    res = await client.post('/users', json=payload)
    return res.json()


@pytest.fixture()
async def user_email(client: AsyncClient) -> Dict:
    """Фикстура: активный пользователь с email."""
    return await _create_user(
        client,
        username='user',
        email='u@u.com',
    )


@pytest.fixture()
async def user_phone(client: AsyncClient) -> Dict:
    """Фикстура: активный пользователь с телефоном."""
    return await _create_user(
        client,
        username='phoneuser',
        email=None,
        phone='79998887766',
    )


async def _get_token(client: AsyncClient, login: str, password: str) -> str:
    """Получить access-token по логину и паролю."""
    data = {'login': login, 'password': password}
    res = await client.post('/auth/login', data=data)
    body = res.json()
    return body.get('access_token', '')


@pytest.fixture()
async def token_email(client: AsyncClient, user_email: Dict) -> str:
    """Фикстура: токен пользователя с email."""
    return await _get_token(client, 'u@u.com', 'qwe123')


@pytest.fixture
async def admin(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession],
) -> Dict:
    """Фикстура: пользователь с правами ADMIN."""
    user_data = await _create_user(
        client, username='admin', email='admin@a.com',
    )
    async with sessionmaker() as session:
        stmt = (
            update(User)
            .where(User.id == user_data['id'])
            .values(role=UserRole.ADMIN)
        )
        await session.execute(stmt)
        await session.commit()
    return user_data


@pytest.fixture
async def manager1(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession],
) -> Dict:
    """Фикстура: первый пользователь с правами MANAGER."""
    user_data = await _create_user(
        client, username='manager1', email='m1@m.com',
    )
    async with sessionmaker() as session:
        stmt = (
            update(User)
            .where(User.id == user_data['id'])
            .values(role=UserRole.MANAGER)
        )
        await session.execute(stmt)
        await session.commit()
    return user_data


@pytest.fixture
async def manager2(
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession],
) -> Dict:
    """Фикстура: второй пользователь с правами MANAGER."""
    user_data = await _create_user(
        client, username='manager2', email='m2@m.com',
    )
    async with sessionmaker() as session:
        stmt = (
            update(User)
            .where(User.id == user_data['id'])
            .values(role=UserRole.MANAGER)
        )
        await session.execute(stmt)
        await session.commit()
    return user_data


@pytest.fixture
async def admin_token(client: AsyncClient, admin: Dict) -> str:
    """Фикстура: токен пользователя ADMIN."""
    return await _get_token(client, 'admin@a.com', 'qwe123')


@pytest.fixture
async def manager1_token(client: AsyncClient, manager1: Dict) -> str:
    """Фикстура: токен первого пользователя MANAGER."""
    return await _get_token(client, 'm1@m.com', 'qwe123')


@pytest.fixture
async def manager2_token(client: AsyncClient, manager2: Dict) -> str:
    """Фикстура: токен второго пользователя MANAGER."""
    return await _get_token(client, 'm2@m.com', 'qwe123')
