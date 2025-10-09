from __future__ import annotations

from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.dish import Dish
from src.repositories.dish import DishRepository


class DishService:
    """Тонкая бизнес-обёртка над репозиторием. Никакого SQL здесь."""

    def __init__(self, session: AsyncSession) -> None:
        self.repo = DishRepository(session)

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
        """Вернуть страницу блюд по фильтрам (поддержка M2M cafe_id)."""
        return await self.repo.list(
            active=active,
            limit=limit,
            offset=offset,
            cafe_id=cafe_id,
            q=q,
            min_price=min_price,
            max_price=max_price,
            available=available,
        )

    async def get(self, dish_id: int) -> Dish | None:
        """Получить блюдо по ID."""
        return await self.repo.get(dish_id)

    async def create(self, **data) -> Dish:
        """Создать блюдо (репозиторий разберёт поля и M2M)."""
        return await self.repo.create(**data)

    async def update(self, dish: Dish, **data) -> Dish:
        """Частично обновить блюдо (replace-семантика для cafe_ids)."""
        return await self.repo.update(dish, **data)

    async def soft_delete(self, dish: Dish) -> None:
        """Soft-delete: active=False."""
        await self.repo.soft_delete(dish)
