import pytest

BASE_URL_CAFES = "/cafes/"
BASE_URL_TABLES = "/cafe/{cafe_id}/tables/"


@pytest.mark.anyio
async def create_test_cafe(client, token, managers=None):
    """Создает тестовое кафе и возвращает его id."""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "Кафе для теста столов",
        "address": "г. Москва, ул. Тестовая, 5",
        "phone": "+7-900-000-00-01"
    }
    if managers:
        data["managers_id"] = managers
    resp = await client.post(BASE_URL_CAFES, json=data, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


@pytest.mark.anyio
async def test_create_table_admin(client, admin_token):
    """Администратор создаёт стол."""
    cafe_id = await create_test_cafe(client, admin_token)
    headers = {"Authorization": f"Bearer {admin_token}"}
    data = {
        "seat_number": 1,
        "description": "Столик у окна"
    }
    resp = await client.post(BASE_URL_TABLES.format(cafe_id=cafe_id), json=data, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["seat_number"] == 1


@pytest.mark.anyio
async def test_create_table_manager(client, manager_token, manager_user):
    """Менеджер создаёт стол в своём кафе."""
    cafe_id = await create_test_cafe(client, manager_token, managers=[manager_user["id"]])
    headers = {"Authorization": f"Bearer {manager_token}"}
    data = {
        "seat_number": 2,
        "description": "Маленький столик"
    }
    resp = await client.post(BASE_URL_TABLES.format(cafe_id=cafe_id), json=data, headers=headers)
    assert resp.status_code == 200, resp.text


@pytest.mark.anyio
async def test_create_table_regular_forbidden(client, regular_token, admin_token):
    """Обычный пользователь не может создавать столы."""
    cafe_id = await create_test_cafe(client, admin_token)
    headers = {"Authorization": f"Bearer {regular_token}"}
    data = {"seat_number": 3, "description": "Пробный столик"}
    resp = await client.post(BASE_URL_TABLES.format(cafe_id=cafe_id), json=data, headers=headers)
    assert resp.status_code in (401, 403), resp.text


@pytest.mark.anyio
async def test_get_all_tables_admin(client, admin_token):
    """Администратор получает список всех столов конкретного кафе."""
    cafe_id = await create_test_cafe(client, admin_token)
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = await client.get(BASE_URL_TABLES.format(cafe_id=cafe_id), headers=headers)
    assert resp.status_code == 200, resp.text
    assert isinstance(resp.json(), list)


@pytest.mark.anyio
async def test_get_table_by_id(client, admin_token):
    """Получение конкретного стола по ID."""
    cafe_id = await create_test_cafe(client, admin_token)
    headers = {"Authorization": f"Bearer {admin_token}"}
    create_data = {"seat_number": 5, "description": "Стол для двоих"}
    create_resp = await client.post(BASE_URL_TABLES.format(cafe_id=cafe_id), json=create_data, headers=headers)
    assert create_resp.status_code == 200, create_resp.text
    table_id = create_resp.json()["id"]

    resp = await client.get(f"/cafe/{cafe_id}/tables/{table_id}", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == table_id


@pytest.mark.anyio
async def test_update_table_admin(client, admin_token):
    """Администратор обновляет данные стола."""
    cafe_id = await create_test_cafe(client, admin_token)
    headers = {"Authorization": f"Bearer {admin_token}"}
    create_data = {"seat_number": 10, "description": "Первое описание"}
    create_resp = await client.post(BASE_URL_TABLES.format(cafe_id=cafe_id), json=create_data, headers=headers)
    assert create_resp.status_code == 200
    table_id = create_resp.json()["id"]

    patch_data = {"description": "Описание обновлено администратором"}
    patch_resp = await client.patch(f"/cafe/{cafe_id}/tables/{table_id}", json=patch_data, headers=headers)
    assert patch_resp.status_code == 200, patch_resp.text
    assert patch_resp.json()["description"] == patch_data["description"]


@pytest.mark.anyio
async def test_deactivate_table_admin(client, admin_token):
    """Администратор может деактивировать стол."""
    cafe_id = await create_test_cafe(client, admin_token)
    headers = {"Authorization": f"Bearer {admin_token}"}

    create_data = {"seat_number": 99, "description": "Стол для деактивации"}
    create_resp = await client.post(BASE_URL_TABLES.format(cafe_id=cafe_id), json=create_data, headers=headers)
    assert create_resp.status_code == 200, create_resp.text
    table_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"/cafe/{cafe_id}/tables/{table_id}",
        json={"is_active": False},
        headers=headers
    )
    assert patch_resp.status_code == 200, patch_resp.text
    assert patch_resp.json()["is_active"] is False


@pytest.mark.anyio
async def test_deactivate_table_manager(client, manager_token, manager_user):
    """Менеджер может деактивировать стол в своём кафе."""
    cafe_id = await create_test_cafe(client, manager_token, managers=[manager_user["id"]])
    headers = {"Authorization": f"Bearer {manager_token}"}

    create_data = {"seat_number": 5, "description": "Стол менеджера"}
    create_resp = await client.post(BASE_URL_TABLES.format(cafe_id=cafe_id), json=create_data, headers=headers)
    assert create_resp.status_code == 200, create_resp.text
    table_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"/cafe/{cafe_id}/tables/{table_id}",
        json={"is_active": False},
        headers=headers
    )
    assert patch_resp.status_code == 200, patch_resp.text
    assert patch_resp.json()["is_active"] is False


@pytest.mark.anyio
async def test_update_table_manager_forbidden_other_cafe(client, admin_token, manager_token):
    """Менеджер не может обновить стол в чужом кафе."""
    cafe_id = await create_test_cafe(client, admin_token)
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    create_data = {"seat_number": 15, "description": "Стол для проверки прав"}
    create_resp = await client.post(BASE_URL_TABLES.format(cafe_id=cafe_id), json=create_data, headers=headers_admin)
    assert create_resp.status_code == 200
    table_id = create_resp.json()["id"]

    headers_manager = {"Authorization": f"Bearer {manager_token}"}
    patch_resp = await client.patch(
        f"/cafe/{cafe_id}/tables/{table_id}",
        json={"description": "Попытка изменить чужой стол"},
        headers=headers_manager
    )
    assert patch_resp.status_code == 403, patch_resp.text


@pytest.mark.anyio
async def test_deactivate_table_manager_forbidden_other_cafe(client, admin_token, manager_token):
    """Менеджер не может деактивировать стол в чужом кафе."""
    cafe_id = await create_test_cafe(client, admin_token)
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    create_data = {"seat_number": 10, "description": "Стол чужого кафе"}
    create_resp = await client.post(BASE_URL_TABLES.format(cafe_id=cafe_id), json=create_data, headers=headers_admin)
    assert create_resp.status_code == 200
    table_id = create_resp.json()["id"]

    headers_manager = {"Authorization": f"Bearer {manager_token}"}
    patch_resp = await client.patch(
        f"/cafe/{cafe_id}/tables/{table_id}",
        json={"is_active": False},
        headers=headers_manager
    )
    assert patch_resp.status_code == 403, patch_resp.text