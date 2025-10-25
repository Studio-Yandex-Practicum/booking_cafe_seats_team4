from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.cafe import Cafe
from models.dish import Dish
from schemas.dish import DishCreate, DishUpdate


class CRUDDish(CRUDBase[Dish, DishCreate, DishUpdate]):
    """CRUD для блюд."""

    async def get_dishes(
        self,
        session: AsyncSession,
        cafe_id: Optional[int] = None,
        only_active: bool = True,
    ) -> List[Dish]:
        """Возвращает список блюд."""
        stmt = select(self.model)
        if only_active:
            stmt = stmt.where(self.model.is_active.is_(True))
        if cafe_id is not None:
            stmt = stmt.join(Dish.cafes).where(Cafe.id == cafe_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        obj_in: DishCreate,
        session: AsyncSession,
    ) -> Dish:
        """Создание блюда с привязкой к кафе."""
        obj_in_data = obj_in.model_dump()
        cafe_ids = obj_in_data.pop("cafes_id", [])
        cafes = []
        if cafe_ids:
            cafes_query = await session.execute(
                select(Cafe).where(Cafe.id.in_(cafe_ids))
            )
            cafes = list(cafes_query.scalars().all())

        db_obj = self.model(**obj_in_data, cafes=cafes)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj: Dish,
        obj_in: DishUpdate,
        session: AsyncSession,
    ) -> Dish:
        """Обновление блюда с обработкой связей с кафе."""
        update_data = obj_in.model_dump(exclude_unset=True)
        cafe_ids = update_data.pop("cafes_id", None)
        if cafe_ids is not None:
            cafes_query = await session.execute(
                select(Cafe).where(Cafe.id.in_(cafe_ids))
            )
            db_obj.cafes = list(cafes_query.scalars().all())
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj


dish_crud = CRUDDish(Dish)
