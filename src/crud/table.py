from typing import Any, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.table import Table
from schemas.table import TableCreate, TableUpdate

from .base import CRUDBase


class CRUDTable(CRUDBase[Table, TableCreate, TableUpdate]):
    """CRUD-операции для модели Table с поддержкой загрузки кафе."""

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


table_crud = CRUDTable(Table)
