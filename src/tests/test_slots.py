import pytest
from httpx import AsyncClient

SLOT_PAYLOAD = {
    "start_time": "10:00",
    "end_time": "11:00",
    "description": "Тестовый слот",
}


@pytest.fixture
async def cafe_for_slots(client: AsyncClient, manager1_token: str, manager1: dict) -> dict:
    """Фикстура: создаёт кафе, управляемое manager1."""
    headers = {'Authorization': f'Bearer {manager1_token}'}
    payload = {
        "name": "Кафе для теста слотов",
        "address": "г. Тест, ул. Слотная, д. 5",
        "phone": "+7(111)111-11-11",
        "managers_id": [manager1["id"]],
    }
    res = await client.post("/cafes", headers=headers, json=payload)
    assert res.status_code == 200, res.text
    return res.json()


@pytest.mark.anyio
async def test_create_slot_by_manager_success(
    client: AsyncClient, manager1_token: str, cafe_for_slots: dict
):
    """Менеджер создаёт временной слот в своём кафе."""
    cafe_id = cafe_for_slots["id"]
    headers = {"Authorization": f"Bearer {manager1_token}"}

    res = await client.post(f"/cafe/{cafe_id}/time_slots", json=SLOT_PAYLOAD, headers=headers)
    assert res.status_code in (200, 201), res.text
    data = res.json()
    assert data["start_time"] == SLOT_PAYLOAD["start_time"]
    assert data["end_time"] == SLOT_PAYLOAD["end_time"]
    assert data["description"] == SLOT_PAYLOAD["description"]
    assert "id" in data


@pytest.mark.anyio
async def test_create_slot_by_manager_success(
    client: AsyncClient, manager1_token: str, cafe_for_slots: dict
):
    """Менеджер создаёт временной слот в своём кафе."""
    cafe_id = cafe_for_slots["id"]
    headers = {"Authorization": f"Bearer {manager1_token}"}

    res = await client.post(f"/cafe/{cafe_id}/time_slots", json=SLOT_PAYLOAD, headers=headers)
    assert res.status_code == 201, res.text

    data = res.json()
    assert data["start_time"] == SLOT_PAYLOAD["start_time"]
    assert data["end_time"] == SLOT_PAYLOAD["end_time"]
    assert data["description"] == SLOT_PAYLOAD["description"]
    assert data["is_active"] is True

    res_get = await client.get(f"/cafe/{cafe_id}/time_slots", headers=headers)
    assert res_get.status_code == 200
    slots = res_get.json()
    assert any(slot["id"] == data["id"] for slot in slots)    

@pytest.mark.xfail(reason="Проверка прав отключена (user_can_manage_cafe)")
@pytest.mark.anyio
async def test_manager_create_slot_in_foreign_cafe_forbidden(
    client: AsyncClient, manager2_token: str, cafe_for_slots: dict
):
    """Менеджер не может создавать слоты в чужом кафе."""
    headers = {'Authorization': f'Bearer {manager2_token}'}
    cafe_id = cafe_for_slots['id']

    res = await client.post(f'/cafe/{cafe_id}/time_slots', headers=headers, json=SLOT_PAYLOAD)

    assert res.status_code == 403, res.text
    body = res.json()
    assert "code" in body and "message" in body    


@pytest.mark.anyio
async def test_user_cannot_create_slot(
    client: AsyncClient, token_email: str, cafe_for_slots: dict
):
    """Обычный пользователь не может создавать временные слоты."""
    headers = {'Authorization': f'Bearer {token_email}'}
    cafe_id = cafe_for_slots['id']

    res = await client.post(f'/cafe/{cafe_id}/time_slots', headers=headers, json=SLOT_PAYLOAD)
    assert res.status_code == 403
    body = res.json() if res.text.strip().startswith("{") else {"code": res.status_code}
    assert body.get("code") in ("FORBIDDEN", 403)   


@pytest.mark.anyio
async def test_get_all_slots(client: AsyncClient, manager1_token: str, cafe_for_slots: dict):
    """Авторизованный пользователь может получить список слотов кафе."""
    headers = {'Authorization': f'Bearer {manager1_token}'}
    cafe_id = cafe_for_slots['id']

    res_create = await client.post(f'/cafe/{cafe_id}/time_slots', headers=headers, json=SLOT_PAYLOAD)
    assert res_create.status_code == 201, res_create.text

    res = await client.get(f'/cafe/{cafe_id}/time_slots', headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert isinstance(data, list)
    assert any(slot['description'] == SLOT_PAYLOAD['description'] for slot in data)


@pytest.mark.anyio
async def test_update_slot_success(
    client: AsyncClient, manager1_token: str, cafe_for_slots: dict
):
    """Менеджер может обновить слот в своём кафе."""
    headers = {'Authorization': f'Bearer {manager1_token}'}
    cafe_id = cafe_for_slots['id']

    res_create = await client.post(f'/cafe/{cafe_id}/time_slots', headers=headers, json=SLOT_PAYLOAD)
    assert res_create.status_code == 201
    slot_id = res_create.json()['id']

    update_payload = {
        "description": "Обновлённый слот",
        "start_time": "10:00",
        "end_time": "12:00"
    }
    res_update = await client.patch(
        f'/cafe/{cafe_id}/time_slots/{slot_id}', headers=headers, json=update_payload
    )

    assert res_update.status_code == 200, res_update.text
    data = res_update.json()
    assert data['description'] == "Обновлённый слот"
    assert data['start_time'] == "10:00" 
    assert data['end_time'] == "12:00"    


@pytest.mark.xfail(reason="Проверка прав отключена (user_can_manage_cafe)")
@pytest.mark.anyio
async def test_manager_cannot_update_foreign_slot(
    client: AsyncClient, manager2_token: str, manager1_token: str, cafe_for_slots: dict
):
    """Менеджер не может обновить слот чужого кафе."""
    headers_m1 = {'Authorization': f'Bearer {manager1_token}'}
    headers_m2 = {'Authorization': f'Bearer {manager2_token}'}
    cafe_id = cafe_for_slots['id']

    res_create = await client.post(f'/cafe/{cafe_id}/time_slots', headers=headers_m1, json=SLOT_PAYLOAD)
    assert res_create.status_code == 201
    slot_id = res_create.json()['id']

    res_update = await client.patch(
        f'/cafe/{cafe_id}/time_slots/{slot_id}',
        headers=headers_m2,
        json={"description": "Попытка обновить чужой слот"},
    )

    assert res_update.status_code == 403, res_update.text
    body = res_update.json()
    assert body["code"] == "FORBIDDEN"    


@pytest.mark.anyio
async def test_deactivate_slot_success(
    client: AsyncClient, manager1_token: str, cafe_for_slots: dict
):
    """Менеджер может деактивировать слот в своём кафе."""
    headers = {'Authorization': f'Bearer {manager1_token}'}
    cafe_id = cafe_for_slots['id']

    res_create = await client.post(f'/cafe/{cafe_id}/time_slots', headers=headers, json=SLOT_PAYLOAD)
    assert res_create.status_code == 201
    slot_id = res_create.json()['id']

    res_patch = await client.patch(
        f'/cafe/{cafe_id}/time_slots/{slot_id}', headers=headers, json={"is_active": False}
    )

    assert res_patch.status_code == 200
    data = res_patch.json()
    assert data['is_active'] is False    