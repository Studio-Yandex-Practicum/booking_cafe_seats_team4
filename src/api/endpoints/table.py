from typing import Annotated, List

import redis
from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, require_manager_or_admin
from api.responses import (FORBIDDEN_RESPONSE, INVALID_ID_RESPONSE,
                           NOT_FOUND_RESPONSE, SUCCESSFUL_RESPONSE,
                           TABLE_NOT_FOUND_IN_CAFE_RESPONSE,
                           UNAUTHORIZED_RESPONSE, VALIDATION_ERROR_RESPONSE)
from api.table_service import TableService
from core.db import get_session
from core.redis import get_redis, redis_cache
from core.decorators.redis import cache_response
from core.constants import EXPIRE_CASHE_TIME
from schemas.table import TableCreate, TableInfo, TableUpdate
from schemas.user import UserInfo

router = APIRouter(prefix='/cafe/{cafe_id}/tables', tags=['Столы'])


@router.get(
    '',
    response_model=List[TableInfo],
    summary='Список столов в кафе',
    responses={
        **SUCCESSFUL_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **INVALID_ID_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
@cache_response(
    cache_key_template="tables:{current_user.role}:{show_all}",
    expire=EXPIRE_CASHE_TIME,
    response_model=TableInfo
)
async def get_all_tables_in_cafe(
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    cafe_id: Annotated[
        int,
        Path(
            description='ID кафе',
        ),
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    show_all: Annotated[
        bool,
        Query(
            description=(
                'Показывать все столы в кафе или нет. '
                'По умолчанию показывает все столы.'
            ),
        ),
    ] = False,
) -> List[TableInfo]:
    """Получение списка доступных для бронирования столов в кафе.

    Для администраторов и менеджеров - все столы (с возможностью выбора),
    для пользователей - только активные.
    """
    return await TableService.get_all_tables(
        session=session,
        cafe_id=cafe_id,
        current_user=current_user,
        show_all=show_all,
    )


@router.get(
    '/{table_id}',
    response_model=TableInfo,
    summary='Информация о столе в кафе по его ID',
    responses={
        **SUCCESSFUL_RESPONSE,
        **TABLE_NOT_FOUND_IN_CAFE_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **INVALID_ID_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
@cache_response(
    cache_key_template="tables:{table_id}",
    expire=EXPIRE_CASHE_TIME,
    response_model=TableInfo
)
async def get_table_by_id(
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    cafe_id: Annotated[
        int,
        Path(
            description='ID кафе',
        ),
    ],
    table_id: Annotated[
        int,
        Path(
            description='ID стола',
        ),
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> TableInfo:
    """Получение информации о столе в кафе по его ID.

    Для администраторов и менеджеров - все столы,
    для пользователей - только активные.
    """
    return await TableService.get_table(
        session=session,
        cafe_id=cafe_id,
        table_id=table_id,
        current_user=current_user,
    )


@router.post(
    '',
    response_model=TableInfo,
    status_code=status.HTTP_200_OK,
    summary='Новый стол в кафе',
    responses={
        **SUCCESSFUL_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
        **INVALID_ID_RESPONSE,
    },
)
async def create_table(
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    cafe_id: Annotated[
        int,
        Path(
            description='ID кафе',
        ),
    ],
    table_in: TableCreate,
    current_user: Annotated[UserInfo, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[UserInfo, Depends(require_manager_or_admin)],
) -> TableInfo:
    """Создание нового стола кафе. Только для администраторов и менеджеров."""
    return await TableService.create_table(
        session=session,
        cafe_id=cafe_id,
        table_in=table_in,
        current_user=current_user,
    )


@router.patch(
    '/{table_id}',
    response_model=TableInfo,
    summary='Обновление информации о столе в кафе по его ID',
    responses={
        **SUCCESSFUL_RESPONSE,
        **TABLE_NOT_FOUND_IN_CAFE_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
        **INVALID_ID_RESPONSE,
    },
)
async def update_table(
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    cafe_id: Annotated[
        int,
        Path(
            description='ID кафе',
        ),
    ],
    table_id: Annotated[
        int,
        Path(
            description='ID стола',
        ),
    ],
    table_in: TableUpdate,
    current_user: Annotated[UserInfo, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[UserInfo, Depends(require_manager_or_admin)],
) -> TableInfo:
    """Обновление информации о столе в кафе по его ID.

    Только для администраторов и менеджеров.
    """

    table = await TableService.update_table(
        session=session,
        cafe_id=cafe_id,
        table_id=table_id,
        table_in=table_in,
        current_user=current_user,
    )
    await redis_cache.delete_pattern('dishes:*')
    return table
