from typing import Annotated, List

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.cafe_service import CafeService
from api.deps import get_current_user, require_manager_or_admin
from api.responses import (
    CAFE_DUPLICATE_RESPONSE,
    FORBIDDEN_RESPONSE,
    INVALID_ID_RESPONSE,
    INVALID_MANAGER_ID_RESPONSE,
    NOT_FOUND_RESPONSE,
    SUCCESSFUL_RESPONSE,
    UNAUTHORIZED_RESPONSE,
    VALIDATION_ERROR_RESPONSE,
)
from core.db import get_session
from models.user import User
from schemas.cafe import CafeCreate, CafeInfo, CafeUpdate

router = APIRouter(prefix='/cafes', tags=['Кафе'])


@router.get(
    '/',
    response_model=List[CafeInfo],
    summary='Список столов в кафе',
    responses={
        **UNAUTHORIZED_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
        **SUCCESSFUL_RESPONSE,
    },
)
async def get_all_cafes(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
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
    return await CafeService.get_all_cafes(
        session,
        current_user,
        show_all,
    )


@router.post(
    '/',
    response_model=CafeInfo,
    status_code=status.HTTP_200_OK,
    summary='Новый стол в кафе',
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
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[User, Depends(require_manager_or_admin)],
) -> CafeInfo:
    """Создает новое кафе. Только для администраторов и менеджеров."""
    return await CafeService.create_cafe(session, cafe_in)


@router.get(
    '/{cafe_id}',
    response_model=CafeInfo,
    summary='Информация о столе в кафе по его ID',
    responses={
        **SUCCESSFUL_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
        **INVALID_ID_RESPONSE,
    },
)
async def get_cafe_by_id(
    cafe_id: Annotated[
        int,
        Path(
            description='ID кафе',
        ),
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CafeInfo:
    """Получение информации о кафе по его ID.

    Для администраторов и менеджеров - все кафе,
    для пользователей - только активные.
    """
    return await CafeService.get_cafe(session, cafe_id, current_user)


@router.patch(
    '/{cafe_id}',
    response_model=CafeInfo,
    summary='Обновление информации о столе в кафе по его ID',
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
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[User, Depends(require_manager_or_admin)],
) -> CafeInfo:
    """Обновление информации о кафе по его ID.

    Только для администраторов и менеджеров.
    """
    return await CafeService.update_cafe(session, cafe_id, cafe_in)
