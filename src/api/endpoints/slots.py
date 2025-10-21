from typing import Annotated, List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, require_manager_or_admin
from api.responses import (
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    UNAUTHORIZED_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
)
from api.validators.slots import (
    cafe_exists,
    slot_active,
    slot_exists,
    user_can_manage_cafe,
    validate_no_time_overlap,
)
from core.db import get_session
from crud.slots import slot_crud
from models.user import User
from schemas.slots import TimeSlotCreate, TimeSlotInfo, TimeSlotUpdate
from schemas.user import UserRole
from api.exceptions import bad_request

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
    #проверка обязательных полей
    if not payload.start_time or not payload.end_time:
        raise bad_request('start_time и end_time обязательны для слота')

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
    slot = await slot_exists(slot_id, session)
    slot_active(slot)
    cafe = await cafe_exists(slot.cafe_id, session)
    user_can_manage_cafe(current_user, cafe)

    # проверка на частичное обновление времени
    if (payload.start_time is not None or payload.end_time is not None) and \
       (payload.start_time is None or payload.end_time is None):
        raise bad_request(
            'Для обновления времени оба поля start_time и end_time обязательны'
        )

    if payload.start_time and payload.end_time:
        await validate_no_time_overlap(payload, session, exclude_id=slot_id)

    if payload.is_active is not None and payload.is_active is False:
        return await slot_crud.deactivate(slot, session)
    return await slot_crud.update(slot, payload, session)
