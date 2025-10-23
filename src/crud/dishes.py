from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.dish import Dish
from models.cafe import Cafe
from schemas.dish import DishCreate, DishUpdate
from crud.base import CRUDBase


class CRUDDish(CRUDBase[Dish, DishCreate, DishUpdate]):
    """CRUD для блюд."""

    async def get_dishes(
        self,
        session: AsyncSession,
        cafe_id: Optional[int] = None,
        only_active: bool = True,
    ) -> List[Dish]:
        """Возвращает список блюд (все или по cafe_id, с фильтром по is_active)."""
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
        obj_in_data = obj_in.model_dump(exclude_unset=True)
        cafe_ids = obj_in_data.pop("cafes_id", [])
        cafes = []
        if cafe_ids:
            cafes_query = await session.execute(select(Cafe).where(Cafe.id.in_(cafe_ids)))
            cafes = list(cafes_query.scalars().all())

        db_obj = self.model(**obj_in_data, cafes=cafes)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)

        audit_event('dish', 'updated', id=db_obj.id)

        return db_obj


dish_crud = CRUDDish(Dish)
