from typing import Any, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.cafe import Cafe
from models.user import User
from schemas.cafe import CafeCreate, CafeUpdate

from .base import CRUDBase


class CRUDCafe(CRUDBase[Cafe, CafeCreate, CafeUpdate]):
    """CRUD-операции для модели Cafe."""

    async def get(self, obj_id: int, session: AsyncSession) -> Cafe | None:
        """Получение кафе с загрузкой связанных менеджеров."""
        query = (
            select(self.model)
            .options(selectinload(self.model.managers))
            .where(self.model.id == obj_id)
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        session: AsyncSession,
        **kwargs: Any,
    ) -> List[Cafe]:
        """Получение всех кафе с загрузкой связанных менеджеров."""
        query = select(self.model).options(selectinload(self.model.managers))
        result = await session.execute(query)
        return result.scalars().all()

    async def create(self, obj_in: CafeCreate, session: AsyncSession) -> Cafe:
        """Создание кафе с обработкой связи many-to-many (managers)."""
        obj_in_data = obj_in.model_dump(exclude={'managers_id'})
        db_cafe = self.model(**obj_in_data)

        if obj_in.managers_id:
            result = await session.execute(
                select(User).where(User.id.in_(obj_in.managers_id)),
            )
            managers = result.scalars().all()

            if len(managers) != len(obj_in.managers_id):
                raise ValueError('Один или несколько ID менеджеров не найдены')

            db_cafe.managers = managers

        session.add(db_cafe)
        await session.commit()
        await session.refresh(db_cafe)
        return db_cafe

    async def update(
        self,
        db_obj: Cafe,
        obj_in: CafeUpdate,
        session: AsyncSession,
    ) -> Cafe:
        """Обновление кафе и связи managers."""
        update_data = obj_in.model_dump(exclude_unset=True)

        # Обновляем обычные поля
        simple_data = {
            k: v for k, v in update_data.items() if k != 'managers_id'
        }
        for field, value in simple_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        # Обрабатываем менеджеров
        if 'managers_id' in update_data:
            managers_id = update_data['managers_id']
            if not managers_id:
                db_obj.managers = []
            else:
                result = await session.execute(
                    select(User).where(User.id.in_(managers_id)),
                )
                managers = result.scalars().all()

                if len(managers) != len(managers_id):
                    raise ValueError(
                        'Один или несколько ID менеджеров не найдены',
                    )

                db_obj.managers = managers

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj


cafe_crud = CRUDCafe(Cafe)
