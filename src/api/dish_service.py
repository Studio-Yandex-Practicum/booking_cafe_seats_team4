from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from api.exceptions import err
from models.dish import Dish
from models.user import User
from schemas.dish import DishCreate, DishUpdate, DishInfo


class DishService:
    """Сервис блюд."""

    def __init__(self, crud):
        self.crud = crud

    async def get(self, dish_id: int, session: AsyncSession) -> DishInfo:
        dish = await self.crud.get(obj_id=dish_id, session=session)
        if not dish:
            raise err(404, f"Блюдо id={dish_id} не найдено", 404)
        return DishInfo.model_validate(dish, from_attributes=True)

    async def create(
            self,
            dish_in: DishCreate,
            user: User,
            session: AsyncSession
    ) -> Dish:
        """Создать новое блюдо."""
        dish = await self.crud.create(obj_in=dish_in, session=session)
        return dish

    async def update(
            self,
            dish_id: int,
            dish_in: DishUpdate,
            user: User,
            session: AsyncSession
    ) -> Dish:
        """Обновить блюдо."""
        dish = await self.get(dish_id, session)
        updated = await self.crud.update(
            db_obj=dish,
            obj_in=dish_in,
            session=session
        )
        return updated

    async def get_list(
        self,
        session: AsyncSession,
        user: User,
        cafe_id: Optional[int] = None,
        show_all: bool = False,
    ) -> List[DishInfo]:
        """Получить список блюд с учетом прав пользователя."""
        only_active = user.role == 0 and not show_all
        dishes_db = await self.crud.get_dishes(
            session=session,
            cafe_id=cafe_id,
            only_active=only_active,
        )
        return [
            DishInfo.model_validate(dish, from_attributes=True)
            for dish in dishes_db
        ]
