from typing import Annotated, List, Annotated

import redis
from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.cafe_service import CafeService
from api.deps import get_current_user, require_manager_or_admin
from api.responses import (CAFE_DUPLICATE_RESPONSE, FORBIDDEN_RESPONSE,
                           INVALID_ID_RESPONSE, INVALID_MANAGER_ID_RESPONSE,
                           NOT_FOUND_RESPONSE, SUCCESSFUL_RESPONSE,
                           UNAUTHORIZED_RESPONSE, VALIDATION_ERROR_RESPONSE)
from core.db import get_session
from core.redis import get_redis, redis_cache
from core.decorators.redis import cache_response
from core.constants import EXPIRE_CASHE_TIME
from schemas.cafe import CafeCreate, CafeInfo, CafeUpdate
from schemas.user import UserInfo

router = APIRouter(prefix='/cafes', tags=['Кафе'])


@router.get(
    '',
    response_model=List[CafeInfo],
    summary='Получение списка кафе',
    responses={
        **UNAUTHORIZED_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
        **SUCCESSFUL_RESPONSE,
    },
)
@cache_response(
    cache_key_template="cafe:{current_user.role}",
    expire=EXPIRE_CASHE_TIME,
    response_model=CafeInfo
)
async def get_all_cafes(
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    show_all: Annotated[
        bool,
        Query(
            description=(
                'Показывать все кафе или нет. '
                'По умолчанию показывает все кафе.'
            ),
        ),
    ] = False,
) -> List[CafeInfo]:
    """Получение списка кафе.

    Для администраторов и менеджеров - все кафе
    (с возможностью выбора), для пользователей - только активные.
    """

    cafes = await CafeService.get_all_cafes(
        session,
        current_user,
        show_all,
    )
    return cafes


@router.post(
    '',
    response_model=CafeInfo,
    status_code=status.HTTP_200_OK,
    summary='Создание нового кафе',
    responses={
        **SUCCESSFUL_RESPONSE,
        **CAFE_DUPLICATE_RESPONSE,
        **INVALID_MANAGER_ID_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def create_cafe(
    cafe_in: CafeCreate,
    current_user: Annotated[UserInfo, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[UserInfo, Depends(require_manager_or_admin)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
) -> CafeInfo:
    """Создает новое кафе. Только для администраторов и менеджеров."""

    cafe = await CafeService.create_cafe(session, cafe_in, current_user)
    await redis_cache.delete_pattern("cafes:*")
    return cafe


@router.get(
    '/{cafe_id}',
    response_model=CafeInfo,
    summary='Получение информации о кафе по его ID',
    responses={
        **SUCCESSFUL_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
        **INVALID_ID_RESPONSE,
    },
)
@cache_response(
    cache_key_template="cafes:{cafe_id}",
    expire=EXPIRE_CASHE_TIME,
    response_model=CafeInfo
)
async def get_cafe_by_id(
    cafe_id: Annotated[
        int,
        Path(
            description='ID кафе',
        ),
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
) -> CafeInfo:
    """Получение информации о кафе по его ID.

    Для администраторов и менеджеров - все кафе,
    для пользователей - только активные.
    """

    return await CafeService.get_cafe(session, cafe_id, current_user)


@router.patch(
    '/{cafe_id}',
    response_model=CafeInfo,
    summary='Обновление информации о кафе по его ID',
    responses={
        **SUCCESSFUL_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **INVALID_MANAGER_ID_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def update_cafe(
    cafe_id: Annotated[
        int,
        Path(
            description='ID кафе',
        ),
    ],
    cafe_in: CafeUpdate,
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[UserInfo, Depends(require_manager_or_admin)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
) -> CafeInfo:
    """Обновление информации о кафе по его ID.

    Только для администраторов и менеджеров.
    """
    cafe = await CafeService.update_cafe(
        session,
        cafe_id,
        cafe_in,
        current_user=current_user,
    )
    await redis_cache.delete_pattern("cafes:*")
    return cafe
