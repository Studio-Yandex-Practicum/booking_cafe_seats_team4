import pytest
from httpx import AsyncClient

TABLE_PAYLOAD = {
    "description": "Столик у окна",
    "seat_number": 2,
}


@pytest.fixture
async def cafe_for_manager1(client: AsyncClient, manager1_token: str, manager1: dict) -> dict:
    """Фикстура: создает кафе, управляемое manager1."""
    headers = {'Authorization': f'Bearer {manager1_token}'}
    payload = {
        'name': "Кафе для Тестов Столов",
        'address': 'г. Тест, ул. Фикстур, д. 2',
        'phone': '+7(111)111-11-11',
        "managers_id": [manager1['id']]
    }
    res = await client.post('/cafes', headers=headers, json=payload)
    assert res.status_code == 200
    return res.json()


@pytest.mark.anyio
async def test_manager_create_table_in_own_cafe_success(
    client: AsyncClient, manager1_token: str, cafe_for_manager1: dict
) -> None:
    """Менеджер может создать стол в своем кафе."""
    headers = {'Authorization': f'Bearer {manager1_token}'}
    cafe_id = cafe_for_manager1['id']

    res = await client.post(f'/cafe/{cafe_id}/tables', headers=headers, json=TABLE_PAYLOAD)

    assert res.status_code == 200
    data = res.json()
    assert data['description'] == TABLE_PAYLOAD['description']
    assert data['cafe']['id'] == cafe_id


@pytest.mark.anyio
async def test_manager_create_table_in_foreign_cafe_forbidden(
    client: AsyncClient, manager2_token: str, cafe_for_manager1: dict
) -> None:
    """Менеджер не может создать стол в чужом кафе."""
    headers = {'Authorization': f'Bearer {manager2_token}'}
    cafe_id = cafe_for_manager1['id']

    res = await client.post(f'/cafe/{cafe_id}/tables', headers=headers, json=TABLE_PAYLOAD)

    assert res.status_code == 403


@pytest.mark.anyio
async def test_update_table_by_owner_manager_success(
    client: AsyncClient, manager1_token: str, cafe_for_manager1: dict
) -> None:
    """Менеджер может обновить стол в своем кафе."""
    headers = {'Authorization': f'Bearer {manager1_token}'}
    cafe_id = cafe_for_manager1['id']

    # 1. Создаем стол
    res_create = await client.post(f'/cafe/{cafe_id}/tables', headers=headers, json=TABLE_PAYLOAD)
    assert res_create.status_code == 200
    table_id = res_create.json()['id']

    # 2. Обновляем его
    update_payload = {"seat_number": 4}
    res_update = await client.patch(f'/cafe/{cafe_id}/tables/{table_id}', headers=headers, json=update_payload)

    assert res_update.status_code == 200
    assert res_update.json()['seat_number'] == 4


@pytest.mark.anyio
async def test_user_cannot_create_table(
    client: AsyncClient, token_email: str, cafe_for_manager1: dict
) -> None:
    """Обычный пользователь не может создать стол."""
    headers = {'Authorization': f'Bearer {token_email}'}
    cafe_id = cafe_for_manager1['id']

    res = await client.post(f'/cafe/{cafe_id}/tables', headers=headers, json=TABLE_PAYLOAD)

    assert res.status_code == 403
