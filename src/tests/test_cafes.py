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
    client: AsyncClient, token_email: str
) -> None:
    """Обычный пользователь не может создавать кафе."""
    headers = {'Authorization': f'Bearer {token_email}'}
    res = await client.post('/cafes', headers=headers, json=CAFE_PAYLOAD)
    assert res.status_code == 403


@pytest.mark.anyio
async def test_manager_cannot_appoint_admin(
    client: AsyncClient, manager1_token: str, admin: dict
) -> None:
    """Менеджер не может назначить админа менеджером кафе."""
    headers = {'Authorization': f'Bearer {manager1_token}'}
    payload = {**CAFE_PAYLOAD, "managers_id": [admin['id']]}

    res = await client.post('/cafes', headers=headers, json=payload)

    assert res.status_code == 403
    assert res.json()['code'] == 'FORBIDDEN'


@pytest.mark.anyio
async def test_cannot_appoint_user_as_manager(
    client: AsyncClient, admin_token: str, user_email: dict
) -> None:
    """Нельзя назначить обычного пользователя менеджером кафе (проверяем от имени админа)."""
    headers = {'Authorization': f'Bearer {admin_token}'}
    payload = {**CAFE_PAYLOAD, "managers_id": [user_email['id']]}

    res = await client.post('/cafes', headers=headers, json=payload)

    assert res.status_code == 400
    assert res.json()['code'] == 'INVALID_ROLE'


@pytest.mark.anyio
async def test_update_own_cafe_by_manager_success(
    client: AsyncClient, manager1_token: str, manager1: dict
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
    client: AsyncClient, manager1_token: str, manager2_token: str, manager2: dict
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

import pytest

BASE_URL = "/cafes/"


@pytest.mark.anyio
async def test_create_cafe_admin(client, admin_token):
    """Администратор может создать кафе."""
    data = {
        "name": "Кафе Уют",
        "description": "Тестовое кафе для проверки API",
        "address": "г. Москва, ул. Пушкина, д. 10",
        "phone": "+7-999-111-22-33",
        "is_active": True
    }

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.post(BASE_URL, json=data, headers=headers)
    assert response.status_code == 200, response.text

    cafe = response.json()
    assert cafe["name"] == data["name"]
    assert "id" in cafe
    assert cafe["is_active"] is True


@pytest.mark.anyio
async def test_create_cafe_manager(client, manager_token):
    """Менеджер тоже может создать кафе."""
    data = {
        "name": "Кафе Менеджера",
        "description": "Кафе созданное менеджером",
        "address": "г. Санкт-Петербург, Невский пр., 5",
        "phone": "+7-911-222-33-44"
    }
    headers = {"Authorization": f"Bearer {manager_token}"}
    response = await client.post(BASE_URL, json=data, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["name"] == data["name"]


@pytest.mark.anyio
async def test_create_cafe_regular_user(client, regular_token):
    """Обычный пользователь не может создать кафе."""
    data = {
        "title": "Кафе пользователя",
        "description": "Обычный пользователь пытается создать кафе",
        "address": "г. Казань, ул. Баумана, 1",
        "phone": "+7-987-333-44-55"
    }

    headers = {"Authorization": f"Bearer {regular_token}"}
    response = await client.post(BASE_URL, json=data, headers=headers)
    assert response.status_code in (403, 401), response.text


@pytest.mark.anyio
async def test_get_all_cafes(client, regular_token):
    """Авторизованный пользователь может получить список кафе."""
    headers = {"Authorization": f"Bearer {regular_token}"}
    response = await client.get(BASE_URL, headers=headers)
    assert response.status_code == 200, response.text


@pytest.mark.anyio
async def test_get_cafe_by_id(client, admin_token):
    """Проверка получения конкретного кафе по ID."""
    cafe_data = {
        "name": "Тестовое кафе для поиска",
        "description": "Проверка получения по id",
        "address": "г. Омск, ул. Ленина, 7",
        "phone": "+7-900-123-45-67",
        "is_active": True
    }
    headers = {"Authorization": f"Bearer {admin_token}"}
    create_response = await client.post(BASE_URL, json=cafe_data, headers=headers)
    assert create_response.status_code == 200, create_response.text

    cafe_id = create_response.json()["id"]

    response = await client.get(f"{BASE_URL}{cafe_id}", headers=headers)
    assert response.status_code == 200, response.text
    cafe = response.json()
    assert cafe["id"] == cafe_id
    assert cafe["name"] == cafe_data["name"]


@pytest.mark.anyio
async def test_update_cafe_admin(client, admin_token):
    """Администратор может обновить информацию о кафе."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    create_data = {
        "name": "Кафе Обновляемое",
        "description": "Первоначальное описание",
        "address": "г. Москва, ул. Ленина, 1",
        "phone": "+7-999-100-00-00"
    }
    create_resp = await client.post(BASE_URL, json=create_data, headers=headers)
    assert create_resp.status_code == 200, create_resp.text
    cafe_id = create_resp.json()["id"]

    patch_data = {
        "description": "Новое описание",
        "phone": "+7-999-222-22-22"
    }
    patch_resp = await client.patch(f"{BASE_URL}{cafe_id}", json=patch_data, headers=headers)
    assert patch_resp.status_code == 200, patch_resp.text

    updated = patch_resp.json()
    assert updated["description"] == patch_data["description"]
    assert updated["phone"] == patch_data["phone"]


@pytest.mark.anyio
async def test_update_cafe_manager_assigned(client, manager_token, manager_user):
    """Менеджер может обновить кафе, где он назначен менеджером."""
    headers = {"Authorization": f"Bearer {manager_token}"}

    create_data = {
        "name": "Кафе Менеджера (назначен)",
        "description": "Описание до обновления",
        "address": "г. СПб, пр. Менеджерская, 1",
        "phone": "+7-900-111-11-11",
        "managers_id": [manager_user["id"]]
    }
    create_resp = await client.post(BASE_URL, json=create_data, headers=headers)
    assert create_resp.status_code == 200, create_resp.text
    cafe_id = create_resp.json()["id"]

    patch_data = {"description": "Описание обновлено менеджером (назначен)"}
    patch_resp = await client.patch(f"{BASE_URL}{cafe_id}", json=patch_data, headers=headers)
    assert patch_resp.status_code == 200, patch_resp.text

    updated = patch_resp.json()
    assert updated["description"] == patch_data["description"]
    assert updated["id"] == cafe_id


@pytest.mark.anyio
async def test_update_cafe_manager_not_assigned(client, manager_token, admin_token):
    """Менеджер не может обновить кафе, где он не назначен."""
    headers_manager = {"Authorization": f"Bearer {manager_token}"}
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    create_data = {
        "name": "Кафе без менеджера",
        "description": "Создано админом",
        "address": "г. Москва, ул. Независимости, 10",
        "phone": "+7-900-222-22-22"
    }
    create_resp = await client.post(BASE_URL, json=create_data, headers=headers_admin)
    assert create_resp.status_code == 200, create_resp.text
    cafe_id = create_resp.json()["id"]

    patch_data = {"description": "Попытка обновления чужого кафе"}
    patch_resp = await client.patch(f"{BASE_URL}{cafe_id}", json=patch_data, headers=headers_manager)
    assert patch_resp.status_code == 403, patch_resp.text


@pytest.mark.anyio
async def test_update_cafe_regular_user_forbidden(client, regular_token):
    """Обычный пользователь не может обновлять кафе."""
    headers = {"Authorization": f"Bearer {regular_token}"}

    patch_data = {"description": "Попытка обновить кафе"}
    response = await client.patch(f"{BASE_URL}1", json=patch_data, headers=headers)
    assert response.status_code in (403, 401), response.text
