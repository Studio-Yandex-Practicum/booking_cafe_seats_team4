from typing import Annotated, List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from validators.slots import (
    cafe_exists,
    slot_active,
    slot_exists,
    user_can_manage_cafe,
)

from api.deps import require_manager_or_admin
from core.db import get_session
from crud.slots import slot_crud
from models.user import User
from schemas.slots import TimeSlotCreate, TimeSlotInfo, TimeSlotUpdate

router = APIRouter(prefix='/cafe/slots', tags=['Временные слоты'])


@router.get('', response_model=List[TimeSlotInfo])
async def list_slots(
    cafe_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> List[TimeSlotInfo]:
    """Список активных временных слотов конкретного кафе (публичный доступ)."""
    cafe = await cafe_exists(cafe_id, session)
    return await slot_crud.get_by_cafe(cafe.id, session)


@router.post(
    '',
    response_model=TimeSlotInfo,
    status_code=status.HTTP_201_CREATED,
)
async def create_slot(
    payload: TimeSlotCreate,
    current_user: Annotated[User, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TimeSlotInfo:
    """Создание временного слота (только менеджер своего кафе или админ)."""
    cafe = await cafe_exists(payload.cafe_id, session)
    user_can_manage_cafe(current_user, cafe)

    new_slot = await slot_crud.create(payload, session)
    return new_slot


@router.get(
    '/{slot_id}',
    response_model=TimeSlotInfo,
)
async def get_slot(
    slot_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TimeSlotInfo:
    """Получить слот по ID (только активный)."""
    slot = await slot_exists(slot_id, session)
    slot_active(slot)
    return slot


@router.patch(
    '/{slot_id}',
    response_model=TimeSlotInfo,
)
async def update_slot(
    slot_id: int,
    payload: TimeSlotUpdate,
    current_user: Annotated[User, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TimeSlotInfo:
    """Обновить временной слот (менеджер своего кафе или админ)."""
    slot = await slot_exists(slot_id, session)
    slot_active(slot)

    cafe = await cafe_exists(slot.cafe_id, session)
    user_can_manage_cafe(current_user, cafe)

    updated = await slot_crud.update(slot, payload, session)
    return updated


@router.delete(
    '/{slot_id}',
    response_model=TimeSlotInfo,
)
async def deactivate_slot(
    slot_id: int,
    current_user: Annotated[User, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TimeSlotInfo:
    """Деактивировать (soft delete) временной слот."""
    slot = await slot_exists(slot_id, session)
    slot_active(slot)

    cafe = await cafe_exists(slot.cafe_id, session)
    user_can_manage_cafe(current_user, cafe)

    deactivated = await slot_crud.deactivate(slot, session)
    return deactivated
