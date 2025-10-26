import pytest
from httpx import AsyncClient

CAFE_PAYLOAD = {
    'name': "Тестовая кофейня",
    'address': 'г. Тест, ул. Юнит, д. 1',
    'phone': '+7(000)000-00-00',
    'description': 'Кофе и тесты',
}


@pytest.mark.anyio
async def test_create_cafe_by_admin_success(client: AsyncClient, admin_token: str):
    headers = {'Authorization': f'Bearer {admin_token}'}
    res = await client.post('/cafes', headers=headers, json=CAFE_PAYLOAD)
    assert res.status_code == 200


@pytest.mark.anyio
async def test_create_cafe_by_manager_success(client: AsyncClient, manager1_token: str):
    headers = {'Authorization': f'Bearer {manager1_token}'}
    res = await client.post('/cafes', headers=headers, json=CAFE_PAYLOAD)
    assert res.status_code == 200


@pytest.mark.anyio
async def test_create_cafe_by_user_forbidden(
    client: AsyncClient, token_email: str,
) -> None:
    """Обычный пользователь не может создавать кафе."""
    headers = {'Authorization': f'Bearer {token_email}'}
    res = await client.post('/cafes', headers=headers, json=CAFE_PAYLOAD)
    assert res.status_code == 403


@pytest.mark.anyio
async def test_manager_cannot_appoint_admin(
    client: AsyncClient, manager1_token: str, admin: dict,
) -> None:
    """Менеджер не может назначить админа менеджером кафе."""
    headers = {'Authorization': f'Bearer {manager1_token}'}
    payload = {**CAFE_PAYLOAD, "managers_id": [admin['id']]}

    res = await client.post('/cafes', headers=headers, json=payload)

    assert res.status_code == 403
    assert res.json()['code'] == 'FORBIDDEN'


@pytest.mark.anyio
async def test_cannot_appoint_user_as_manager(
    client: AsyncClient, admin_token: str, user_email: dict,
) -> None:
    """Нельзя назначить обычного пользователя менеджером кафе (проверяем от имени админа)."""
    headers = {'Authorization': f'Bearer {admin_token}'}
    payload = {**CAFE_PAYLOAD, "managers_id": [user_email['id']]}

    res = await client.post('/cafes', headers=headers, json=payload)

    assert res.status_code == 400
    assert res.json()['code'] == 'INVALID_ROLE'


@pytest.mark.anyio
async def test_update_own_cafe_by_manager_success(
    client: AsyncClient, manager1_token: str, manager1: dict,
) -> None:
    """Менеджер может обновить информацию в своем кафе."""
    headers = {'Authorization': f'Bearer {manager1_token}'}
    # 1. Создаем кафе, где manager1 является управляющим
    create_payload = {**CAFE_PAYLOAD, "managers_id": [manager1['id']]}
    res_create = await client.post('/cafes', headers=headers, json=create_payload)
    assert res_create.status_code == 200
    cafe_id = res_create.json()['id']

    # 2. Обновляем это кафе
    update_payload = {"description": "Новое описание"}
    res_update = await client.patch(f'/cafes/{cafe_id}', headers=headers, json=update_payload)

    assert res_update.status_code == 200
    assert res_update.json()['description'] == "Новое описание"


@pytest.mark.anyio
async def test_update_foreign_cafe_by_manager_forbidden(
    client: AsyncClient, manager1_token: str, manager2_token: str, manager2: dict,
) -> None:
    """Менеджер не может обновить чужое кафе."""
    # 1. manager2 создает свое кафе
    headers_m2 = {'Authorization': f'Bearer {manager2_token}'}
    create_payload = {**CAFE_PAYLOAD, "name": "Кафе Менеджера 2",
                      "managers_id": [manager2['id']]}
    res_create = await client.post('/cafes', headers=headers_m2, json=create_payload)
    assert res_create.status_code == 200
    cafe_id = res_create.json()['id']

    # 2. manager1 пытается его обновить
    headers_m1 = {'Authorization': f'Bearer {manager1_token}'}
    update_payload = {"description": "Попытка взлома"}
    res_update = await client.patch(f'/cafes/{cafe_id}', headers=headers_m1, json=update_payload)

    assert res_update.status_code == 403
