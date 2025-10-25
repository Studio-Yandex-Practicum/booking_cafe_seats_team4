from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from api.responses import (
    BAD_RESPONSE,
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    UNAUTHORIZED_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
)
from api.validators.booking import (
    admin_or_manager_check,
    ban_change_status,
    booking_exists,
    cafe_exists,
    check_all_objects,
    check_booking_date,
    check_current_user_booking,
    user_can_manage_cafe,
)
from core.db import get_session
from core.redis import get_redis, redis_cache
from core.decorators.redis import cache_response
from core.constants import EXPIRE_CASHE_TIME
from crud.booking import booking_crud
from models.user import User
from schemas.booking import BookingCreate, BookingInfo, BookingUpdate

router = APIRouter(prefix='/booking', tags=['Бронирования'])


@router.get('/', response_model=List[BookingInfo],
            summary='Список бронирований',
            responses={
                **UNAUTHORIZED_RESPONSE,
                **VALIDATION_ERROR_RESPONSE},
            )
@cache_response(
    cache_key_template="booking:{user.role}:{show_all}",
    expire=EXPIRE_CASHE_TIME,
    response_model=BookingInfo
)
async def get_list_booking(
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    show_all: Optional[bool] = False,
    cafe_id: Optional[int] = None,
    user_id: Optional[int] = None,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> List[BookingInfo]:
    """Получение списка бронирований.

    Для администраторов и менеджеров - все бронирования (с возможностью
    фильтрации), для обычных пользователей - только свои бронирования.
    """

    if cafe_id:
        await cafe_exists(cafe_id, session)
    if not await admin_or_manager_check(user):
        return await booking_crud.get_multi_booking(
            session=session,
            cafe_id=cafe_id,
            user_id=user.id,
        )
    return await booking_crud.get_multi_booking(
        session=session,
        show_all=show_all,
        cafe_id=cafe_id,
        user_id=user_id,
    )


@router.post('/', response_model=BookingInfo,
             summary='Создание бронирования',
             responses={
                 **UNAUTHORIZED_RESPONSE,
                 **VALIDATION_ERROR_RESPONSE,
                 **BAD_RESPONSE},
             )
async def create_booking(
    booking: BookingCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> BookingInfo:
    """Создает новое бронирования.

    Только для авторизированных пользователей.
    """
    await check_booking_date(booking.booking_date)
    await check_all_objects(
        booking.cafe_id,
        booking.slots_id,
        booking.tables_id,
        booking.booking_date,
        session,
    )
    return await booking_crud.create_booking(
        booking,
        user.id,
        session,
    )


@router.get('/{booking_id}', response_model=BookingInfo,
            summary='Информация о бронировании по ID',
            responses={
                **UNAUTHORIZED_RESPONSE,
                **VALIDATION_ERROR_RESPONSE,
                **FORBIDDEN_RESPONSE,
                **BAD_RESPONSE,
                **NOT_FOUND_RESPONSE},
            )
async def get_booking(
    booking_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> BookingInfo:
    """Получение информации о бронировании по его ID.

    Для администраторов и менеджеров - доступны все бронирования,
    для обычных пользователей - только свои бронирования.
    """
    if not await admin_or_manager_check(user):
        return await booking_crud.get_booking_current_user(
            booking_id,
            user,
            session,
        )
    return await booking_exists(booking_id, session)


@router.patch('/{booking_id}', response_model=BookingInfo,
              summary='Обновление бронирования по ID',
              responses={
                  **UNAUTHORIZED_RESPONSE,
                  **VALIDATION_ERROR_RESPONSE,
                  **FORBIDDEN_RESPONSE,
                  **BAD_RESPONSE,
                  **NOT_FOUND_RESPONSE},
              )
async def update_booking(
    booking_id: int,
    obj_in: BookingUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> BookingInfo:
    """Обновление информации о бронировании по его ID.

    Для администраторов и менеджеров - доступны все бронирования,
    для обычных пользователей - только свои бронирования.
    """
    if not await admin_or_manager_check(user):
        booking = await check_current_user_booking(
            booking_id,
            user,
            session,
        )
    else:
        booking = await booking_exists(booking_id, session)
        await user_can_manage_cafe(user, booking.cafe_id, session)
    slots_id = [slot.id for slot in booking.slots_id]
    tables_id = [table.id for table in booking.tables_id]
    await check_all_objects(
            booking.cafe_id,
            slots_id,
            tables_id,
            booking.booking_date,
            session,
            booking.id,
        )
    await ban_change_status(booking, obj_in)
    return await booking_crud.update(booking, obj_in, session)
