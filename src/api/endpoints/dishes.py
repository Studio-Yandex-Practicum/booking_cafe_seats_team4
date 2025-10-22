from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, require_manager_or_admin
from api.validators.users import check_user_is_manager_or_admin
from core.db import get_session
from crud.dishes import dish_crud
from models.dish import Dish
from models.user import User
from schemas.dish import DishCreate, DishInfo, DishUpdate

from ..validators.dishes import (
    check_cafe_exists,
    check_dish,
    check_dish_exists,
    check_name_unique,
)

router = APIRouter(prefix='/dishes', tags=['Блюда'])


@router.get(
    '',
    response_model=List[DishInfo],
    summary=(
        'Получение списка блюд. Для администраторов и менеджеров - все блюда'
        '(с возможностью выбора), для пользователей - только активные.'
    ),
)
async def get_dishes(
    cafe_id: Optional[int] = Query(
        default=None,
        description=(
            'ID кафе, в котором показывать блюда.'
            'Если не задано - показывает все блюда во всех кафе'
        ),
    ),
    only_active: Optional[bool] = Query(
        default=False,
        description=(
            'Показывать все блюда или нет. По умолчанию показывает все блюда'
        ),
        alias='show_all',
    ),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Optional[List[DishInfo]]:
    """Получить список блюд."""
    if check_user_is_manager_or_admin(current_user):
        all_dishes = await dish_crud.get_dishes(
            session,
            cafe_id,
            only_active,
        )
    else:
        all_dishes = await dish_crud.get_dishes(session, cafe_id)
    return all_dishes


@router.post(
    '',
    response_model=DishInfo,
    summary='Создает новое блюда. Только для администраторов и менеджеров.',
)
async def create_dich(
    dish_in: DishCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_manager_or_admin),
) -> Dish:
    """Создает новое блюда. Только для администраторов и менеджеров."""
    await check_name_unique(session, dish_in.name)
    cafes = await check_cafe_exists(session, dish_in.cafes_id)
    return await dish_crud.create_dish(session, dish_in, cafes)


@router.get(
    '/{dish_id}',
    response_model=DishInfo,
    summary='Получение информации о блюде по его ID',
)
async def get_dish(
    dish_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Dish:
    """Получение информации о блюде по его ID.

    Для администраторов и менеджеров - все блюда,
    для пользователей - только активные.
    """
    dish = await dish_crud.get(dish_id, session)
    return check_dish(dish, current_user)


@router.patch(
    '/{dish_id}',
    response_model=DishInfo,
    summary='Обновление информации о блюде по его ID',
)
async def update_dish(
    dish_id: int,
    obj_in: DishUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_manager_or_admin),
) -> Dish:
    """Обновление информации о блюде по его ID."""
    dish = await dish_crud.get(dish_id, session)
    check_dish_exists(dish)
    return await dish_crud.update_dish(
        session,
        dish,
        obj_in,
    )
