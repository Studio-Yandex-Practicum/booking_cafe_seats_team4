from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, require_manager_or_admin
from api.validators.dishes import check_cafe_exists, check_name_unique, check_dish
from api.validators.users import check_user_is_manager_or_admin
from core.db import get_session
from core.logging import get_user_logger
from crud.dishes import dish_crud
from models.user import User
from schemas.dish import DishCreate, DishInfo, DishUpdate
from dish_service import DishService

router = APIRouter(prefix="/dishes", tags=["Блюда"])
dish_service = DishService(crud=dish_crud)


@router.get("", response_model=List[DishInfo])
async def get_dishes(
    cafe_id: Optional[int] = Query(None),
    show_all: bool = Query(False, description="Показать все блюда"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[DishInfo]:
    """Получить список блюд."""
    is_staff = check_user_is_manager_or_admin(current_user)
    dishes = await dish_crud.get_dishes(
        session=session,
        cafe_id=cafe_id,
        only_active=not is_staff and not show_all,
    )
    return dishes


@router.post("", response_model=DishInfo)
async def create_dish(
    dish_in: DishCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_manager_or_admin),
):
    """Создание нового блюда."""
    await check_name_unique(session, dish_in.name)
    await check_cafe_exists(session, dish_in.cafes_id)
    dish = await dish_service.create(dish_in, current_user, session)
    logger = get_user_logger(__name__, current_user)
    logger.info(f"Блюдо создано: id={dish.id}, name='{dish.name}'")
    return dish


@router.get("/{dish_id}", response_model=DishInfo)
async def get_dish(
    dish_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    dish = await dish_service.get(dish_id, session)
    return check_dish(dish, current_user)


@router.patch("/{dish_id}", response_model=DishInfo)
async def update_dish(
    dish_id: int,
    obj_in: DishUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_manager_or_admin),
):
    """Обновление блюда."""
    dish = await dish_service.update(dish_id, obj_in, current_user, session)
    return dish
