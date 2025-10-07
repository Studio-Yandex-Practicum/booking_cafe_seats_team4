from __future__ import annotations
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

PositiveInt = Annotated[int, Field(ge=1)]
Money = Annotated[Decimal, Field(ge=0)]
NameStr = Annotated[str, Field(min_length=1, max_length=200)]


class DishBase(BaseModel):
    """Базовая схема блюда (общие поля)."""

    name: NameStr
    price: Money
    description: str | None = None
    is_available: bool = True
    media_id: UUID | None = None
    active: bool = True


class DishCreate(DishBase):
    """Схема создания блюда."""
    cafe_ids: list[int] = Field(default_factory=list,
                                description="ID кафе, где доступно блюдо")


class DishUpdate(BaseModel):
    """Схема частичного обновления блюда."""
    name: NameStr | None = None
    price: Money | None = None
    description: str | None = None
    is_available: bool | None = None
    media_id: UUID | None = None
    active: bool | None = None
    cafe_ids: list[int] | None = Field(None,
                                       description="Полная замена списка кафе")


class DishOut(DishBase):
    """Схема вывода блюда в ответе API."""
    id: int
    # ▶ Можно добавить cafe_ids при необходимости
    # cafe_ids: list[int] = []
    model_config = ConfigDict(from_attributes=True)
