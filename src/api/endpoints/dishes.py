from typing import List, Optional, Annotated

import redis
from fastapi import APIRouter, Depends, Query

from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, require_manager_or_admin
from api.dish_service import DishService
from api.validators.dishes import (check_cafe_exists, check_dish_access,
                                   check_name_unique)
from core.db import get_session
from core.logging import get_user_logger
from core.redis import get_redis, redis_cache
from core.decorators.redis import cache_response
from core.constants import EXPIRE_CASHE_TIME
from crud.dishes import dish_crud
from models.user import User
from schemas.dish import DishCreate, DishInfo, DishUpdate

router = APIRouter(prefix="/dishes", tags=["Блюда"])
dish_service = DishService(crud=dish_crud)


@router.get(
    "",
    response_model=List[DishInfo],
    summary="Получение списка блюд",
    description=(
        "Для администраторов и менеджеров - все блюда, "
        "для пользователей - только активные."
    )
)
@cache_response(
    cache_key_template="dishes:{current_user.role}",
    expire=EXPIRE_CASHE_TIME,
    response_model=DishInfo
)
async def get_dishes(
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    cafe_id: Optional[int] = Query(None, description="ID кафе для фильтрации"),
    show_all: bool = Query(
        False,
        description="Показать все блюда (только для staff)"
    ),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[DishInfo]:
    """Получить список блюд."""

    return await dish_service.get_list(
        session=session,
        user=current_user,
        cafe_id=cafe_id,
        show_all=show_all,
    )


@router.post(
    "",
    response_model=DishInfo,
    summary="Создание нового блюда",
    description="Только для администраторов и менеджеров."
)
async def create_dish(
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    dish_in: DishCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_manager_or_admin),
) -> DishInfo:
    """Создание нового блюда."""
    await check_name_unique(session, dish_in.name)
    await check_cafe_exists(session, dish_in.cafes_id)
    dish = await dish_service.create(dish_in, current_user, session)
    logger = get_user_logger(__name__, current_user)
    logger.info(f"Блюдо создано: id={dish.id}, name='{dish.name}'")
    await redis_cache.delete_pattern('dishes:*')
    return dish


@router.get(
    "/{dish_id}",
    response_model=DishInfo,
    summary="Получение информации о блюде",
    description=(
        "Для администраторов и менеджеров - все блюда, "
        "для пользователей - только активные."
    )
)
@cache_response(
    cache_key_template="dishes:{dish_id}",
    expire=EXPIRE_CASHE_TIME,
    response_model=DishInfo
)
async def get_dish(
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    dish_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DishInfo:
    """Получение информации о блюде по его ID."""
    dish = await dish_service.get(dish_id, session)
    return check_dish_access(dish, current_user)


@router.patch(
    "/{dish_id}",
    response_model=DishInfo,
    summary="Обновление информации о блюде",
    description="Только для администраторов и менеджеров."
)
async def update_dish(
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    dish_id: int,
    obj_in: DishUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_manager_or_admin),
) -> DishInfo:
    """Обновление блюда."""
    if obj_in.name is not None:
        await check_name_unique(session, obj_in.name)
    if obj_in.cafes_id is not None:
        await check_cafe_exists(session, obj_in.cafes_id)
    dish = await dish_service.update(dish_id, obj_in, current_user, session)
    await redis_cache.delete_pattern('disches:*')
    return dish
