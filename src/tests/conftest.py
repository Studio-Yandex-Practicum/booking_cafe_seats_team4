from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Generator

import pytest
import importlib

import api.validators.slots as slot_validators
import api.endpoints.slots as slots_endpoints

def _disable_user_can_manage_cafe():
    """Отключаем проверку user_can_manage_cafe для всех тестов."""
    def always_true(*args, **kwargs):
        return True

    slot_validators.user_can_manage_cafe = always_true
    slots_endpoints.user_can_manage_cafe = always_true

    importlib.reload(slots_endpoints)

_disable_user_can_manage_cafe()

from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session as ORMSession
from sqlalchemy import update
from models.user import User
from schemas.user import UserRole

from core.config import settings
from core.db import get_session
from main import app


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
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> Dict:
    """Фикстура: пользователь с правами ADMIN."""
    user_data = await _create_user(
        client, username='admin', email='admin@a.com'
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
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> Dict:
    """Фикстура: первый пользователь с правами MANAGER."""
    user_data = await _create_user(
        client, username='manager1', email='m1@m.com'
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
    client: AsyncClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> Dict:
    """Фикстура: второй пользователь с правами MANAGER."""
    user_data = await _create_user(
        client, username='manager2', email='m2@m.com'
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


# ==============================
# Пользователи разных ролей
# ==============================

@pytest.fixture
async def admin_user(sessionmaker, client):
    """Создаёт пользователя и повышает до администратора через ORM."""
    data = {
        "username": "admin_user",
        "email": "admin@mail.ru",
        "password": "adminpass"
    }
    response = await client.post("/users", json=data)
    assert response.status_code == 200, response.text
    user = response.json()

    async with sessionmaker() as session:
        await session.execute(
            update(User)
            .where(User.id == user["id"])
            .values(role=2)
        )
        await session.commit()
    return user


@pytest.fixture
async def manager_user(sessionmaker, client):
    """Создаёт пользователя и повышает до менеджера через ORM."""
    data = {
        "username": "manager_user",
        "email": "manager@mail.ru",
        "password": "managerpass"
    }
    response = await client.post("/users", json=data)
    assert response.status_code == 200, response.text
    user = response.json()

    async with sessionmaker() as session:
        await session.execute(
            update(User)
            .where(User.id == user["id"])
            .values(role=1)
        )
        await session.commit()
    return user


@pytest.fixture
async def regular_user(client):
    """Создает обычного пользователя."""
    data = {
        "username": "regular_user",
        "email": "user@mail.ru",
        "password": "userpass"
    }
    response = await client.post("/users", json=data)
    assert response.status_code == 200, response.text
    return response.json()


# ==============================
# Токены для авторизации
# ==============================

@pytest.fixture
async def admin_token(client, admin_user):
    """Возвращает токен администратора."""
    response = await client.post(
        "/auth/login",
        data={"login": admin_user["email"], "password": "adminpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture
async def manager_token(client, manager_user):
    """Возвращает токен менеджера."""
    response = await client.post(
        "/auth/login",
        data={"login": manager_user["email"], "password": "managerpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture
async def regular_token(client, regular_user):
    """Возвращает токен обычного пользователя."""
    response = await client.post(
        "/auth/login",
        data={"login": regular_user["email"], "password": "userpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


# ==============================
# ORM-пользователи для тестов
# ==============================

@pytest.fixture
async def orm_admin(sessionmaker, admin):
    """Возвращает ORM-объект администратора."""
    async with sessionmaker() as session:
        from models.user import User
        result = await session.get(User, admin["id"])
        return result


@pytest.fixture
async def orm_manager1(sessionmaker, manager1):
    """Возвращает ORM-объект manager1 для использования в тестах."""
    async with sessionmaker() as session:
        from models.user import User
        result = await session.get(User, manager1["id"])
        return result


@pytest.fixture
async def orm_manager2(sessionmaker, manager2):
    """Возвращает ORM-объект manager2 для использования в тестах."""
    async with sessionmaker() as session:
        from models.user import User
        result = await session.get(User, manager2["id"])
        return result