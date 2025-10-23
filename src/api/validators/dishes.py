from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.exceptions import bad_request, not_found
from models.cafe import Cafe
from models.dish import Dish
from models.user import User
from schemas.user import UserRole


async def check_name_unique(session: AsyncSession, obj_name: str) -> None:
    """Проверяет существование имени в бд."""
    query = await session.execute(select(Dish).where(Dish.name == obj_name))
    dish = query.scalars().first()
    if dish:
        raise bad_request(f'Блюдо {obj_name} уже существует.')
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
        raise bad_request(f'Кафе с id {missing_ids} не существуют.')
    return found_cafes


def check_dish_exists(dish: Optional[Dish]) -> Dish:
    """Проверка существования объекта dish."""
    if dish is None:
        raise bad_request('Такого блюда не существует.')
    return dish


def check_dish(dish: Optional[Dish], user: User) -> Dish:
    """Проверка, существует ли блюдо, активно ли оно, статус юзера."""
    dish = check_dish_exists(dish)

    if dish and (dish.is_active is False and user.role == UserRole.USER):
        raise not_found('Это блюдо сейчас недоступно.')
    return dish
