from typing import Annotated, List

import redis
from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user_optional, require_manager_or_admin
from api.exceptions import err
from api.responses import (FORBIDDEN_RESPONSE, NOT_FOUND_RESPONSE,
                           UNAUTHORIZED_RESPONSE, VALIDATION_ERROR_RESPONSE)
from api.validators.slots import (cafe_exists, slot_exists,
                                  user_can_manage_cafe,
                                  validate_no_time_overlap)
from core.db import get_session
from core.decorators.redis import cache_response
from core.constants import EXPIRE_CASHE_TIME
from crud.slots import slot_crud
from core.redis import get_redis, redis_cache
from models.user import User
from schemas.slots import TimeSlotCreate, TimeSlotInfo, TimeSlotUpdate
from schemas.user import UserRole

router = APIRouter(
    prefix='/cafe/{cafe_id}/time_slots',
    tags=['Временные слоты']
)


@router.get(
    '',
    response_model=List[TimeSlotInfo],
    summary='Получить список временных слотов кафе',
    responses={
        **NOT_FOUND_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
@cache_response(
    cache_key_template="slots:{user.role}",
    expire=EXPIRE_CASHE_TIME,
    response_model=TimeSlotInfo
)
async def list_slots(
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    cafe_id: Annotated[int, Path(description='ID кафе')],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    session: Annotated[AsyncSession, Depends(get_session)],
    show_all: bool = False,
) -> List[TimeSlotInfo]:
    """Вернуть список слотов кафе."""
    cafe = await cafe_exists(cafe_id, session)

    only_active = True
    if show_all and current_user and current_user.role in (
        int(UserRole.ADMIN),
        int(UserRole.MANAGER)
    ):
        only_active = False

    slots = await slot_crud.get_by_cafe(cafe.id, session, only_active)
    return [TimeSlotInfo.model_validate(
        slot, from_attributes=True) for slot in slots]


@router.post(
    '',
    response_model=TimeSlotInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Создать временной слот',
    responses={
        **UNAUTHORIZED_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
        **NOT_FOUND_RESPONSE,
    },
)
async def create_slot(
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    cafe_id: Annotated[int, Path(description='ID кафе')],
    payload: TimeSlotCreate,
    current_user: Annotated[User, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TimeSlotInfo:
    """Создание временного слота."""
    cafe = await cafe_exists(cafe_id, session)
    user_can_manage_cafe(current_user, cafe)
    await validate_no_time_overlap(payload, session, cafe_id)
    slot = await slot_crud.create_with_cafe_id(
        payload,
        session,
        cafe_id=cafe_id)
    await redis_cache.delete_pattern('slots:*')
    return TimeSlotInfo.model_validate(slot, from_attributes=True)


@router.get(
    '/{slot_id}',
    response_model=TimeSlotInfo,
    summary='Получить слот по ID',
    responses={
        **NOT_FOUND_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
@cache_response(
    cache_key_template="slots:{slot_id}",
    expire=EXPIRE_CASHE_TIME,
    response_model=TimeSlotInfo
)
async def get_time_slot_by_id(
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    cafe_id: Annotated[int, Path(description='ID кафе')],
    slot_id: Annotated[int, Path(description='ID слота')],
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
) -> TimeSlotInfo:
    """Вернуть активный слот по ID."""
    await cafe_exists(cafe_id, session)
    slot = await slot_exists(slot_id, session)
    if slot.cafe_id != cafe_id:
        raise err('NOT_FOUND', 'Слот не найден в данном кафе', 404)
    if (
        not current_user or current_user.role == UserRole.USER
    ) and not slot.is_active:
        raise err('NOT_FOUND', 'Слот не найден', 404)
    if current_user and current_user.role == UserRole.MANAGER:
        cafe = await cafe_exists(cafe_id, session)
        user_can_manage_cafe(current_user, cafe)
    return TimeSlotInfo.model_validate(slot, from_attributes=True)


@router.patch(
    '/{slot_id}',
    response_model=TimeSlotInfo,
    summary='Обновить или деактивировать слот',
    responses={
        **UNAUTHORIZED_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
        **NOT_FOUND_RESPONSE,
    },
)
async def update_time_slot_by_id(
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    cafe_id: Annotated[int, Path(description='ID кафе')],
    slot_id: Annotated[int, Path(description='ID слота')],
    payload: TimeSlotUpdate,
    current_user: Annotated[User, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TimeSlotInfo:
    """Обновить параметры слота или деактивировать его."""
    cafe = await cafe_exists(cafe_id, session)
    slot = await slot_exists(slot_id, session)
    if slot.cafe_id != cafe_id:
        raise err('NOT_FOUND', 'Слот не найден в данном кафе', 404)
    user_can_manage_cafe(current_user, cafe)

    if (payload.start_time is not None or payload.end_time is not None) and (
        payload.start_time is None or payload.end_time is None
    ):
        raise err(
            'BAD_REQUEST',
            'Для обновления времени поля start_time и end_time обязательны',
            400)

    if payload.start_time and payload.end_time:
        await validate_no_time_overlap(
            payload,
            session,
            cafe_id,
            exclude_id=slot_id
        )
    updated_slot = await slot_crud.update(slot, payload, session)
    await redis_cache.delete_pattern('slots:*')
    return TimeSlotInfo.model_validate(updated_slot, from_attributes=True)
