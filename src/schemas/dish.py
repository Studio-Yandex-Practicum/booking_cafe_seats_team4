from __future__ import annotations

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

# Удобные типы с ограничениями
PositiveInt = Annotated[int, Field(ge=1)]
Money = Annotated[Decimal, Field(ge=0)]
NameStr = Annotated[str, Field(min_length=1, max_length=200)]


class DishBase(BaseModel):
    """Базовая схема блюда (без привязки к одному кафе)."""

    name: NameStr
    price: Money
    description: str | None = None
    is_available: bool = True
    media_id: UUID | None = None
    active: bool = True


class DishCreate(DishBase):
    """Создание блюда."""

    cafe_ids: list[PositiveInt] | None = None


class DishUpdate(BaseModel):
    """Частичное обновление блюда."""

    name: NameStr | None = None
    price: Money | None = None
    description: str | None = None
    is_available: bool | None = None
    media_id: UUID | None = None
    active: bool | None = None
    cafe_ids: list[PositiveInt] | None = None


class DishOut(DishBase):
    """Ответ с блюдом."""

    id: int
    cafe_ids: list[PositiveInt] = []
    model_config = ConfigDict(from_attributes=True)
