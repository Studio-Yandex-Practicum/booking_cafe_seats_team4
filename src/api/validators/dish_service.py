from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.logging import get_user_logger
from api.exceptions import err
from models.dish import Dish
from models.cafe import Cafe
from schemas.dish import DishCreate, DishUpdate
from crud.base import CRUDBase


class DishService:
    """Сервис блюд."""

    def __init__(self, crud: CRUDBase):
        self.crud = crud

    async def get(self, dish_id: int, session: AsyncSession) -> Dish:
        dish = await self.crud.get(obj_id=dish_id, session=session)
        if not dish:
            raise err("NOT_FOUND", f"Блюдо id={dish_id} не найдено", 404)
        return dish

    async def create(self, dish_in: DishCreate, user, session: AsyncSession) -> Dish:
        logger = get_user_logger(__name__, user)
        cafes = await session.execute(select(Cafe).where(Cafe.id.in_(dish_in.cafes_id)))
        found_cafes = list(cafes.scalars().all())
        if len(found_cafes) != len(dish_in.cafes_id):
            raise err("CAFE_NOT_FOUND", "Некоторые кафе не существуют", 404)

        dish = Dish(
            name=dish_in.name,
            description=dish_in.description,
            photo_id=dish_in.photo_id,
            price=dish_in.price,
            cafes=found_cafes,
        )
        session.add(dish)
        await session.commit()
        await session.refresh(dish)
        logger.info(f"Создано блюдо: id={dish.id}, name='{dish.name}'")
        return dish

    async def update(self, dish_id: int, dish_in: DishUpdate, user, session: AsyncSession) -> Dish:
        logger = get_user_logger(__name__, user)
        dish = await self.crud.get(obj_id=dish_id, session=session)
        if not dish:
            raise err("NOT_FOUND", f"Блюдо id={dish_id} не найдено", 404)

        if not dish.is_active:
            raise err("DISH_INACTIVE", "Нельзя изменять неактивное блюдо", 403)

        updated = await self.crud.update(obj_current=dish, obj_in=dish_in, session=session)
        logger.info(f"Обновлено блюдо: id={dish.id}, name='{dish.name}'")
        return updated
