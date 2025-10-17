from typing import Any, Dict

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_create_user_ok(client: AsyncClient) -> None:
    """Создание пользователя по email -200."""
    body = {
        'username': 'alice',
        'password': 'qwe123',
        'email': 'a@a.com',
    }
    r = await client.post('/users', json=body)
    assert r.status_code == 200
    data = r.json()
    assert data['username'] == 'alice'
    assert data['email'] == 'a@a.com'


@pytest.mark.anyio
async def test_create_user_duplicate_email(
    client: AsyncClient,
    user_email: Dict[str, Any],
) -> None:
    """Дубликат email запрещён - 400."""
    body = {
        'username': 'alice2',
        'password': 'qwe123',
        'email': 'u@u.com',
    }
    r = await client.post('/users', json=body)
    assert r.status_code == 400
    data = r.json()
    assert data['code'] == 400


@pytest.mark.anyio
async def test_create_user_no_contacts(client: AsyncClient) -> None:
    """Нет email и phone - 400."""
    body = {'username': 'bob', 'password': 'qwe123'}
    r = await client.post('/users', json=body)
    assert r.status_code == 400
    data = r.json()
    assert data['code'] == 400


@pytest.mark.anyio
async def test_me_requires_auth(client: AsyncClient) -> None:
    """/users/me без токена - 401."""
    r = await client.get('/users/me')
    assert r.status_code == 401
    data = r.json()
    assert data['code'] == 401


@pytest.mark.anyio
async def test_create_user_with_phone_only_ok(client: AsyncClient) -> None:
    """Создание пользователя только с phone -200."""
    body = {
        'username': 'bob_phone',
        'password': 'qwe123',
        'phone': '79990000000',
    }
    r = await client.post('/users', json=body)
    assert r.status_code == 200
    data = r.json()
    assert data['username'] == 'bob_phone'
    assert data.get('phone') == '79990000000'
    assert ('email' not in data) or (data['email'] in (None, ''))


@pytest.mark.anyio
async def test_create_user_with_both_contacts_ok(client: AsyncClient) -> None:
    """Создание пользователя с email и phone -200."""
    body = {
        'username': 'charlie',
        'password': 'qwe123',
        'email': 'c@c.com',
        'phone': '79992223344',
    }
    r = await client.post('/users', json=body)
    assert r.status_code == 200
    data = r.json()
    assert data['username'] == 'charlie'
    assert data.get('email') == 'c@c.com'
    assert data.get('phone') == '79992223344'


@pytest.mark.anyio
async def test_create_user_duplicate_phone(
    client: AsyncClient,
    user_phone: Dict[str, Any],
) -> None:
    """Дубликат phone запрещён - 400."""
    body = {
        'username': 'dup-phone',
        'password': 'qwe123',
        'phone': '79998887766',
    }
    r = await client.post('/users', json=body)
    assert r.status_code == 400
    data = r.json()
    assert data['code'] == 400


@pytest.mark.anyio
async def test_create_user_missing_password_validation_error(
    client: AsyncClient,
) -> None:
    """Нет обязательного password - 422."""
    body = {'username': 'no-pass', 'email': 'np@np.com'}
    r = await client.post('/users', json=body)
    assert r.status_code == 422
    data = r.json()
    assert data['code'] == 422


# Дубликат username разрешён — ОК (200), создаётся второй пользователь
@pytest.mark.anyio
async def test_create_user_duplicate_username_allowed(
    client: AsyncClient,
    user_email: Dict[str, Any],
) -> None:
    """Дубликат username допускается - ожидаем 200 и новый id."""
    body = {
        'username': 'user',
        'password': 'qwe123',
        'email': 'another@a.com',
    }
    r = await client.post('/users', json=body)
    assert r.status_code == 200
    data = r.json()
    assert data['username'] == 'user'
    assert data['email'] == 'another@a.com'
    assert data['id'] != user_email['id']
