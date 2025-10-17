from typing import Any, Dict

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_login_invalid_credentials(
    client: AsyncClient,
    user_email: Dict[str, Any],
) -> None:
    """Неверный пароль - 422."""
    form = {'login': 'u@u.com', 'password': 'wrong'}
    r = await client.post('/auth/login', data=form)
    assert r.status_code == 422
    data = r.json()
    assert data['code'] == 422


@pytest.mark.anyio
async def test_login_ok_and_get_me(
    client: AsyncClient,
    user_email: Dict[str, Any],
) -> None:
    """Успешный логин по email и /users/me - 200."""
    form = {'login': 'u@u.com', 'password': 'qwe123'}
    r = await client.post('/auth/login', data=form)
    assert r.status_code == 200
    token = r.json()['access_token']

    headers = {'Authorization': f'Bearer {token}'}
    me = await client.get('/users/me', headers=headers)
    assert me.status_code == 200
    assert me.json()['email'] == 'u@u.com'


@pytest.mark.anyio
async def test_change_own_role_forbidden(
    client: AsyncClient,
    token_email: str,
) -> None:
    """Сам себе роль менять нельзя - 403."""
    headers = {'Authorization': f'Bearer {token_email}'}
    r = await client.patch('/users/me', headers=headers, json={'role': 2})
    assert r.status_code == 403
    data = r.json()
    assert data['code'] == 403


@pytest.mark.anyio
async def test_login_with_phone_ok_and_get_me(
    client: AsyncClient,
    user_phone: Dict[str, Any],
) -> None:
    """Логин по телефону и /users/me - 200."""
    form = {'login': '79998887766', 'password': 'qwe123'}
    r = await client.post('/auth/login', data=form)
    assert r.status_code == 200
    token = r.json()['access_token']

    headers = {'Authorization': f'Bearer {token}'}
    me = await client.get('/users/me', headers=headers)
    assert me.status_code == 200
    body = me.json()
    assert body.get('phone') == '79998887766'


@pytest.mark.anyio
async def test_me_with_invalid_token_unauthorized(client: AsyncClient) -> None:
    """Невалидный токен для /users/me - 401."""
    headers = {'Authorization': 'Bearer invalid-token'}
    r = await client.get('/users/me', headers=headers)
    assert r.status_code == 401
    data = r.json()
    assert data['code'] == 401


@pytest.mark.anyio
async def test_login_missing_password_validation_error(
    client: AsyncClient,
    user_email: Dict[str, Any],
) -> None:
    """Нет пароля в логине - 422."""
    form = {'login': 'u@u.com'}
    r = await client.post('/auth/login', data=form)
    assert r.status_code == 422
    data = r.json()
    assert data['code'] == 422


@pytest.mark.anyio
async def test_login_unknown_user(client: AsyncClient) -> None:
    """Неизвестный пользователь - 422."""
    form = {'login': 'noone@example.com', 'password': 'qwe123'}
    r = await client.post('/auth/login', data=form)
    assert r.status_code == 422
    data = r.json()
    assert data['code'] == 422
