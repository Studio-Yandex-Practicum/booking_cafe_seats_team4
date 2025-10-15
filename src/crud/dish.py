from __future__ import annotations

from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.dish import Dish
from models.cafe import Cafe


class CRUDDish(CRUDBase[Dish, object, object]):
    """
    CRUD-слой для модели Dish.

    Содержит методы для работы с блюдами:
    - получение одного или списка блюд с фильтрацией,
    - создание, обновление, мягкое удаление.
    """

    def __init__(self) -> None:
        super().__init__(Dish)

    async def get(self, session: AsyncSession, dish_id: int) -> Dish | None:
        """Получить блюдо по ID (делегируется базовому CRUD)."""
        return await super().get(dish_id, session)

    async def get_multi(
        self,
        session: AsyncSession,
        *,
        only_active: bool | None = None,
        cafe_id: int | None = None,
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
            filters.append(Dish.is_active.is_(True))
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
        cafe_ids: Iterable[int],
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
        cafe_ids: Iterable[int] | None = None,
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
            dish.is_active = active
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
        dish.is_active = False
        await session.flush()


dish_crud = CRUDDish()
