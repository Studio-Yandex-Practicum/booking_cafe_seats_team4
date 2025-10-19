from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.models.cafe import Cafe
from src.models.dish import Dish
from src.models.user import User
from src.schemas.user import UserRole

logger = get_logger(__name__)


async def check_name_unique(session: AsyncSession, obj_name: str) -> None:
    """Проверяет существование имени в бд."""
    query = await session.execute(select(Dish).where(Dish.name == obj_name))
    dish = query.scalars().first()
    if dish:
        logger.error(f'Дублирование названия блюда {obj_name=}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Блюдо {obj_name} уже существует.',
        )
    return


async def check_cafe_exists(
        session: AsyncSession,
        cafe_id: List[int],
) -> List[Cafe]:
    """Проверить существование кафе по id."""
    query = select(Cafe).where(Cafe.id.in_(cafe_id))
    res_query = await session.execute(query)
    found_cafes = list(res_query.scalars().all())
    found_ids = {int(cafe.id) for cafe in found_cafes}
    missing_ids = set(cafe_id) - found_ids
    if missing_ids:
        logger.error(f'cafe_id = {missing_ids} не существует.')
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Кафе с id {missing_ids} не существуют.',
            )
    return found_cafes


def check_dish_exists(dish: Optional[Dish]) -> Dish:
    """Проверка существования объекта dish."""
    if dish is None:
        logger.error('Запрос несуществующего блюда.')
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Такого блюда не существует.',
        )
    return dish


def check_dish(dish: Optional[Dish], user: User) -> Dish:
    """Проверка, существует ли блюдо, активно ли оно, статус юзера."""
    dish = check_dish_exists(dish)

    if dish and (dish.is_active is False and user.role == UserRole.USER):
        logger.error(
            f'Пользователь {user.username=} запросил неактивное блюдо.',
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Это блюдо сейчас недоступно.',
        )
    return dish
