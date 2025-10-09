from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Optional, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.cafe import Cafe
from src.models.dish import Dish


class DishRepository:
    """Вся работа с БД/ORM для блюд. Здесь же фильтры и M2M-фильтр по cafe_id."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ---------- READ ----------
    async def list(
        self,
        *,
        active: Optional[bool],
        limit: int,
        offset: int,
        cafe_id: Optional[int] = None,
        q: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        available: Optional[bool] = None,
    ) -> Sequence[Dish]:
        """Вернуть страницу блюд по фильтрам:
        - cafe_id: M2M через связь с Cafe
        - q: подстрока в имени (ilike)
        - min/max_price: диапазон цены
        - available: Dish.is_available
        - active: soft-delete флаг
        """
        stmt = (
            select(Dish)
            .options(selectinload(Dish.cafes))
            .order_by(Dish.created_at.desc())
        )

        if active is not None:
            stmt = stmt.where(Dish.active == active)

        if available is not None:
            stmt = stmt.where(Dish.is_available == available)

        if q:
            stmt = stmt.where(Dish.name.ilike(f'%{q.strip()}%'))

        if min_price is not None:
            stmt = stmt.where(Dish.price >= min_price)

        if max_price is not None:
            stmt = stmt.where(Dish.price <= max_price)

        if cafe_id is not None:
            # Фильтр по кафе через отношение (JOIN по Dish.cafes)
            stmt = stmt.join(Dish.cafes).where(Cafe.id == cafe_id).distinct()

        stmt = stmt.limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get(self, dish_id: int) -> Dish | None:
        """Найти блюдо по PK, с подгруженными кафе."""
        stmt = (
            select(Dish)
            .options(selectinload(Dish.cafes))
            .where(Dish.id == dish_id)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    # ---------- CREATE ----------
    async def create(
        self,
        *,
        name: str,
        price,
        description: Optional[str],
        is_available: bool,
        media_id,
        active: bool,
        cafe_ids: Optional[Iterable[int]] = None,
    ) -> Dish:
        """Создать блюдо и (опционально) синхронизировать M2M
        с кафе по cafe_ids.
        """
        dish = Dish(
            name=name,
            price=price,
            description=description,
            is_available=is_available,
            media_id=media_id,
            active=active,
        )
        self.session.add(dish)
        await self.session.flush()  # dish.id уже доступен

        if cafe_ids:
            dish.cafes = list(await self._load_cafes(cafe_ids))

        await self.session.commit()
        await self.session.refresh(dish)
        return dish

    # ---------- UPDATE ----------
    async def update(
        self,
        dish: Dish,
        *,
        name: Optional[str] = None,
        price=None,
        description: Optional[str] = None,
        is_available: Optional[bool] = None,
        media_id=None,
        active: Optional[bool] = None,
        cafe_ids: Optional[Iterable[int]] = None,
    ) -> Dish:
        """Частично обновить блюдо. Если переданы cafe_ids — заменить набор кафе."""
        if name is not None:
            dish.name = name
        if price is not None:
            dish.price = price
        if description is not None:
            dish.description = description
        if is_available is not None:
            dish.is_available = is_available
        if media_id is not None:
            dish.media_id = media_id
        if active is not None:
            dish.active = active

        if cafe_ids is not None:
            dish.cafes = list(await self._load_cafes(cafe_ids))

        await self.session.commit()
        await self.session.refresh(dish)
        return dish

    # ---------- SOFT DELETE ----------
    async def soft_delete(self, dish: Dish) -> None:
        """Пометить блюдо как неактивное (active=False)."""
        await self.session.execute(
            update(Dish).where(Dish.id == dish.id).values(active=False),
        )
        await self.session.commit()

    # ---------- HELPERS ----------
    async def _load_cafes(self, ids: Iterable[int]) -> Sequence[Cafe]:
        """Подгрузить Cafe по списку идентификаторов.
        Отсутствующие ID игнорируются.
        """
        id_list = list(ids or [])
        if not id_list:
            return []
        res = await self.session.execute(
            select(Cafe).where(Cafe.id.in_(id_list)),
        )
        return res.scalars().all()
