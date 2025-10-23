from sqlalchemy.ext.asyncio import AsyncSession
from core.logging import get_user_logger
from api.exceptions import err
from schemas.dish import DishCreate, DishUpdate
from models.dish import Dish
from models.cafe import Cafe


class DishService:
    """Сервис блюд."""

    def __init__(self, crud):
        self.crud = crud

    async def get(self, dish_id: int, session: AsyncSession) -> Dish:
        dish = await self.crud.get(obj_id=dish_id, session=session)
        if not dish:
            raise err("NOT_FOUND", f"Блюдо id={dish_id} не найдено", 404)
        return dish

    async def create(self, dish_in: DishCreate, user, session: AsyncSession) -> Dish:
        logger = get_user_logger(__name__, user)
        dish = await self.crud.create(obj_in=dish_in, session=session)
        logger.info(f"Создано блюдо: id={dish.id}, name='{dish.name}'")
        return dish

    async def update(self, dish_id: int, dish_in: DishUpdate, user, session: AsyncSession) -> Dish:
        logger = get_user_logger(__name__, user)
        dish = await self.crud.get(obj_id=dish_id, session=session)
        if not dish:
            raise err("NOT_FOUND", f"Блюдо id={dish_id} не найдено", 404)
        if not dish.is_active:
            raise err("DISH_INACTIVE", "Нельзя изменять неактивное блюдо", 403)
        updated = await self.crud.update(db_obj=dish, obj_in=dish_in, session=session)
        logger.info(f"Обновлено блюдо: id={dish.id}, name='{dish.name}'")
        return updated
