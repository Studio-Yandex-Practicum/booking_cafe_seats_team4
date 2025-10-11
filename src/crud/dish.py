from __future__ import annotations

from typing import Iterable
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.dish import Dish
from src.models.cafe import Cafe


class CRUDDish:
    """
    CRUD-слой для модели Dish.

    Содержит методы для работы с блюдами:
    - получение одного или списка блюд с фильтрацией,
    - создание, обновление, мягкое удаление.
    """

    async def get(self, session: AsyncSession, dish_id: UUID) -> Dish | None:
        """Получить блюдо по ID."""
        stmt = select(Dish).where(Dish.id == dish_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_multi(
        self,
        session: AsyncSession,
        *,
        only_active: bool | None = None,
        cafe_id: UUID | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[Dish]]:
        """
        Получить список блюд с фильтрацией и пагинацией.

        Фильтры:
        - only_active: только активные блюда
        - cafe_id: блюда, связанные с конкретным кафе
        - q: поиск по имени
        """
        filters = []
        if only_active is True:
            filters.append(Dish.active.is_(True))
        if q:
            ilike = f"%{q.lower()}%"
            filters.append(func.lower(Dish.name).like(ilike))
        if cafe_id:
            stmt_ids = (
                select(Dish.id)
                .join(Dish.cafes)
                .where(Cafe.id == cafe_id)
            )
            filters.append(Dish.id.in_(stmt_ids))

        total_stmt = select(func.count()).select_from(
            select(Dish.id).where(*filters).subquery())
        items_stmt = (
            select(Dish)
            .where(*filters)
            .order_by(Dish.name.asc())
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
        name: str,
        description: str | None,
        price,
        photo: str | None,
        cafe_ids: Iterable[UUID],
    ) -> Dish:
        """Создать новое блюдо и связать его с кафе (если указаны cafe_ids)."""
        dish = Dish(name=name,
                    description=description,
                    price=price,
                    photo=photo)
        if cafe_ids:
            cafes = (await session.execute(select(Cafe).where(
                Cafe.id.in_(list(cafe_ids))))).scalars().all()
            dish.cafes = cafes
        session.add(dish)
        await session.flush()
        return dish

    async def update(
        self,
        session: AsyncSession,
        dish: Dish,
        *,
        name: str | None = None,
        description: str | None = None,
        price=None,
        photo: str | None = None,
        active: bool | None = None,
        cafe_ids: Iterable[UUID] | None = None,
    ) -> Dish:
        """Обновить существующее блюдо (частично)."""
        if name is not None:
            dish.name = name
        if description is not None:
            dish.description = description
        if price is not None:
            dish.price = price
        if photo is not None:
            dish.photo = photo
        if active is not None:
            dish.active = active
        if cafe_ids is not None:
            cafes = []
            if cafe_ids:
                cafes = (await session.execute(select(Cafe).where(
                    Cafe.id.in_(list(cafe_ids))))).scalars().all()
            dish.cafes = cafes

        await session.flush()
        return dish

    async def soft_delete(self, session: AsyncSession, dish: Dish) -> None:
        """Мягкое удаление блюда — просто снимает активность."""
        dish.active = False
        await session.flush()


dish_crud = CRUDDish()
