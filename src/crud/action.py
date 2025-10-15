from __future__ import annotations

from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.action import Action
from models.cafe import Cafe


class CRUDAction(CRUDBase[Action, object, object]):
    """CRUD-слой для модели Action."""

    def __init__(self) -> None:
        super().__init__(Action)

    async def get(
            self, session: AsyncSession, action_id: int) -> Action | None:
        """Получить акцию по ID (делегируется базовому CRUD)."""
        return await super().get(action_id, session)

    async def get_multi(
        self,
        session: AsyncSession,
        *,
        only_active: bool | None = None,
        cafe_id: int | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[Action]]:
        """Получить список акций с фильтрацией и пагинацией."""
        filters = []
        if only_active is True:
            filters.append(Action.is_active.is_(True))
        if q:
            ilike = f"%{q.lower()}%"
            filters.append(func.lower(Action.description).like(ilike))
        if cafe_id:
            stmt_ids = (
                select(Action.id)
                .join(Action.cafes)
                .where(Cafe.id == cafe_id)
            )
            filters.append(Action.id.in_(stmt_ids))

        total_stmt = select(func.count()).select_from(
            select(Action.id).where(*filters).subquery()
        )
        items_stmt = (
            select(Action)
            .where(*filters)
            .order_by(Action.id.asc())
            .limit(limit)
            .offset(offset)
        )

        total = (await session.execute(total_stmt)).scalar_one()
        items = (await session.execute(items_stmt)).scalars().all()
        return total, items

    async def create(
        self,
        session: AsyncSession,
        *,
        description: str,
        photo_id,
        cafe_ids: Iterable[int],
    ) -> Action:
        """Создать новую акцию и связать её с кафе (если указаны cafe_ids)."""
        action = Action(description=description, photo_id=photo_id)
        if cafe_ids:
            cafes = (
                await session.execute(select(Cafe).where(Cafe.id.in_(
                    list(cafe_ids))))
            ).scalars().all()
            action.cafes = cafes
        session.add(action)
        await session.flush()
        return action

    async def update(
        self,
        session: AsyncSession,
        action: Action,
        *,
        description: str | None = None,
        photo_id=None,
        active: bool | None = None,
        cafe_ids: Iterable[int] | None = None,
    ) -> Action:
        """Обновить существующую акцию (частично)."""
        if description is not None:
            action.description = description
        if photo_id is not None:
            action.photo_id = photo_id
        if active is not None:
            action.is_active = active
        if cafe_ids is not None:
            cafes: list[Cafe] = []
            if cafe_ids:
                cafes = (
                    await session.execute(
                        select(Cafe).where(Cafe.id.in_(list(cafe_ids)))
                    )
                ).scalars().all()
            action.cafes = cafes

        await session.flush()
        return action

    async def soft_delete(self, session: AsyncSession, action: Action) -> None:
        """Мягкое удаление акции — просто снимает активность."""
        action.is_active = False
        await session.flush()


action_crud = CRUDAction()
