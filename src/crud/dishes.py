from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import CRUDBase
from src.models.dish import Dish
from src.models.cafe import Cafe
from src.crud.base import CreateSchemaType, UpdateSchemaType
from src.core.logging import get_logger
from src.api.validators.dishes import check_cafe_exists


logger = get_logger(__name__)


class CRUDDish(CRUDBase):
    """CRUD операции для взаимодействия с таблицей dishes. """

    async def get_dishes(
            self,
            session: AsyncSession,
            cafe_id: Optional[int],
            only_active: Optional[bool] = True,
            ) -> List[Dish]:
        """
        Возвращает список блюд.

        Все или для указанного cafe_id, с фильтром по is_active.
        """
        # logging
        stmt = select(self.model)
        if only_active:
            stmt = stmt.where(self.model.is_active.is_(True))
        if cafe_id is not None:
            stmt = stmt.where(self.model.cafe_id == cafe_id)
        result = await session.execute(stmt)
        dishes = list(result.scalars().all())
        # logging
        return dishes

    async def create_dish(
            self,
            session: AsyncSession,
            obj_in: CreateSchemaType,
            cafes: List[Cafe],
    ) -> Dish:
        """Создаёт новый объект в таблице Dish."""
        obj_in_data = obj_in.model_dump(exclude={'cafes_id'})
        db_obj = self.model(**obj_in_data, cafes=cafes)
        session.add(db_obj)
        await session.commit()
        # logging
        return db_obj

    async def update_dish(
        self,
        session: AsyncSession,
        db_obj: Dish,
        obj_in: UpdateSchemaType,
    ):
        """Частичное обновление объекта Dish."""

        update_data = obj_in.model_dump(exclude_unset=True)
        if update_data['cafes_id'] and update_data['cafes_id'] is not None:
            cafes = await check_cafe_exists(session, update_data['cafes_id'])
            db_obj.cafes = cafes
            del update_data['cafes_id']
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        # logging
        return db_obj


dish_crud = CRUDDish(Dish)
