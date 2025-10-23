from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.action import Action
from models.cafe import Cafe
from schemas.action import ActionCreate, ActionUpdate

from .base import CRUDBase, audit_event


class CRUDActions(CRUDBase[Action, ActionCreate, ActionUpdate]):
    """CRUD-операции для модели Action."""

    async def get(
        self,
        obj_id: int,
        session: AsyncSession,
        show_all: bool = False,
    ) -> Action | None:
        """Получить акцию с загрузкой связанных кафе."""
        result = (
            select(self.model)
            .options(selectinload(self.model.cafes))
            .where(self.model.id == obj_id)
        )
        if not show_all:
            result = result.where(self.model.is_active.is_(True))
        result = await session.execute(result)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        session: AsyncSession,
        show_all: bool = False,
        cafe_id: Optional[int] = None,
    ) -> List[Action]:
        """Получить все акции с фильтрацией по активности и кафе."""
        result = select(self.model).options(selectinload(self.model.cafes))
        if not show_all:
            result = result.where(self.model.is_active.is_(True))
        if cafe_id is not None:
            result = result.join(self.model.cafes).where(Cafe.id == cafe_id)
        result = await session.execute(result)
        return result.scalars().all()

    async def create(
        self,
        obj_in: ActionCreate,
        session: AsyncSession,
    ) -> Action:
        """Создание акции с обработкой связи many-to-many c кафе."""
        obj_in_data = obj_in.model_dump(exclude={'cafes_id'})
        db_action = self.model(**obj_in_data)
        if obj_in.cafes_id:
            result = await session.execute(
                select(Cafe).where(Cafe.id.in_(obj_in.cafes_id)),
            )
            cafes = result.scalars().all()
            if len(cafes) != len(obj_in.cafes_id):
                raise ValueError('Один или несколько кафе не найдены')
            db_action.cafes = cafes
        session.add(db_action)
        await session.commit()
        await session.refresh(db_action)

        audit_event('action', 'created', id=db_action.id)

        return db_action

    async def update(
        self,
        db_obj: Action,
        obj_in: ActionUpdate,
        session: AsyncSession,
    ) -> Action:
        """Обновление акции и связи с кафе."""
        update_data = obj_in.model_dump(exclude_unset=True)
        simple_data = {k: v for k, v in update_data.items() if k != 'cafes_id'}
        for field, value in simple_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        if 'cafes_id' in update_data:
            cafes_id = update_data['cafes_id']
            if not cafes_id:
                db_obj.cafes = []
            else:
                result = await session.execute(
                    select(Cafe).where(Cafe.id.in_(cafes_id)),
                )
                cafes = result.scalars().all()

                if len(cafes) != len(cafes_id):
                    raise ValueError(
                        'Один или несколько кафе не найдены',
                    )

                db_obj.cafes = cafes

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)

        audit_event('action', 'updated', id=db_obj.id)

        return db_obj


actions_crud = CRUDActions(Action)
