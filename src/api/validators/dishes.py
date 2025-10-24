from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.exceptions import bad_request, not_found
from models.dish import Dish
from models.cafe import Cafe
from models.user import User


async def check_name_unique(session: AsyncSession, obj_name: str) -> None:
    """Проверяет, что блюда с таким именем ещё нет."""
    query = await session.execute(select(Dish).where(Dish.name == obj_name))
    dish = query.scalars().first()
    if dish:
        raise bad_request(f"Блюдо '{obj_name}' уже существует.")


async def check_cafe_exists(
        session: AsyncSession,
        cafe_ids: List[int]
) -> List[Cafe]:
    """Проверяет, что все кафе существуют."""
    query = select(Cafe).where(Cafe.id.in_(cafe_ids))
    res = await session.execute(query)
    cafes = list(res.scalars().all())
    found_ids = {c.id for c in cafes}
    missing = set(cafe_ids) - found_ids
    if missing:
        raise bad_request(f"Кафе с id {missing} не существуют.")
    return cafes


def check_dish_access(dish: Dish, user: User) -> Dish:
    """Проверяет доступ к блюду (активность + права пользователя)."""
    if not dish.is_active and user.role == 0:
        raise not_found("Это блюдо сейчас недоступно.")
    return dish
