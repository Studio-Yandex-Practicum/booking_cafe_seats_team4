from typing import Any, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.table import Table
from schemas.table import TableCreate, TableUpdate

from .base import CRUDBase


class CRUDTable(CRUDBase[Table, TableCreate, TableUpdate]):
    """CRUD-операции для модели Table с поддержкой загрузки кафе."""

    async def create(
        self,
        obj_in: TableCreate,
        session: AsyncSession,
        *,
        cafe_id: int,
    ) -> Table:
        """Создает новый стол.

        Добавляет `cafe_id` из URL и переопределяет базовый метод create.
        """
        obj_in_data = obj_in.model_dump()
        obj_in_data['cafe_id'] = cafe_id

        db_obj = self.model(**obj_in_data)

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def get_multi(
        self,
        session: AsyncSession,
        **filters: Any,
    ) -> List[Table]:
        """Получает список столов с подгрузкой связанного кафе."""
        query = select(self.model).options(selectinload(self.model.cafe))

        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        result = await session.execute(query)
        return result.scalars().all()

    async def get(
        self,
        obj_id: int,
        session: AsyncSession,
    ) -> Table | None:
        """Получает один стол по ID с подгрузкой кафе."""
        query = (
            select(self.model)
            .options(selectinload(self.model.cafe))
            .where(self.model.id == obj_id)
        )
        result = await session.execute(query)
        return result.scalars().first()

    async def update(
        self,
        db_obj: Table,
        obj_in: TableUpdate,
        session: AsyncSession,
    ) -> Table:
        """Обновляет стол с контролируемой загрузкой relationships."""
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)

        return db_obj


table_crud = CRUDTable(Table)
