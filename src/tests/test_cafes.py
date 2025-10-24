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
