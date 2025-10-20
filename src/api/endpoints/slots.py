from typing import Annotated, List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, require_manager_or_admin
from api.validators.slots import (
    cafe_exists,
    slot_active,
    slot_exists,
    user_can_manage_cafe,
    validate_no_time_overlap,
)
from api.responses import (
    NOT_FOUND_RESPONSE,
    FORBIDDEN_RESPONSE,
    UNAUTHORIZED_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
)
from core.db import get_session
from crud.slots import slot_crud
from models.user import User
from schemas.slots import TimeSlotCreate, TimeSlotInfo, TimeSlotUpdate
from schemas.user import UserRole

router = APIRouter(prefix='/cafe/slots', tags=['Временные слоты'])


@router.get(
    '',
    response_model=List[TimeSlotInfo],
    summary='Получить список временных слотов кафе',
    description=(
        'Показывает все активные слоты. '
        'Менеджер или администратор могут запросить все, включая неактивные.'
    ),
    responses={
        **NOT_FOUND_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def list_slots(
    cafe_id: int,
    current_user: Annotated[User | None, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    show_all: bool = False,
) -> List[TimeSlotInfo]:
    """Список активных или всех временных слотов конкретного кафе."""
    cafe = await cafe_exists(cafe_id, session)

    only_active = True
    if show_all and current_user:
        if current_user.role in (int(UserRole.ADMIN), int(UserRole.MANAGER)):
            only_active = False

    return await slot_crud.get_by_cafe(cafe.id, session, only_active)


@router.post(
    '',
    response_model=TimeSlotInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Создать временной слот',
    description='Создание доступно только менеджеру данного кафе.',
    responses={
        **UNAUTHORIZED_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
        **NOT_FOUND_RESPONSE,
    },
)
async def create_slot(
    payload: TimeSlotCreate,
    current_user: Annotated[User, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TimeSlotInfo:
    """Создание временного слота."""
    cafe = await cafe_exists(payload.cafe_id, session)
    user_can_manage_cafe(current_user, cafe)
    await validate_no_time_overlap(payload, session)
    return await slot_crud.create(payload, session)


@router.get(
    '/{slot_id}',
    response_model=TimeSlotInfo,
    summary='Получить слот по ID',
    responses={
        **NOT_FOUND_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
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
    summary='Обновить или деактивировать слот',
    description='Менеджер своего кафе или администратор могут изменить слот.',
    responses={
        **UNAUTHORIZED_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
        **NOT_FOUND_RESPONSE,
    },
)
async def update_slot(
    slot_id: int,
    payload: TimeSlotUpdate,
    current_user: Annotated[User, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TimeSlotInfo:
    """Обновить временной слот или деактивировать его."""
    slot = await slot_exists(slot_id, session)
    slot_active(slot)
    cafe = await cafe_exists(slot.cafe_id, session)
    user_can_manage_cafe(current_user, cafe)
    # Проверка пересечения по времени
    await validate_no_time_overlap(payload, session, exclude_id=slot_id)
    # Если is_active=False → деактивируем слот
    if payload.is_active is not None and payload.is_active is False:
        return await slot_crud.deactivate(slot, session)
    return await slot_crud.update(slot, payload, session)