from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


Price = Annotated[Decimal, Field(ge=0, examples=["349.90"])]


class DishBase(BaseModel):
    """
    Базовая схема для блюда.

    Используется для общих полей в схемах создания и вывода.
    """
    name: str = Field(max_length=200, examples=["Маргарита"])
    description: str | None = Field(
        default=None,
        examples=["Классическая пицца с томатами и моцареллой"])
    price: Price
    photo: str | None = Field(
        default=None,
        examples=["c3bb6a7f-2c0a-4d4b-8b6e-0b4f2a2ad9a7"])


class DishCreate(DishBase):
    """
    Схема создания блюда.

    Позволяет указать список кафе, в которых блюдо доступно.
    """
    cafe_ids: list[int] = Field(default_factory=list)


class DishUpdate(BaseModel):
    """
    Схема обновления блюда.

    Все поля необязательные, можно частично обновить запись.
    """
    name: str | None = Field(default=None, max_length=200)
    description: str | None = None
    price: Price | None = None
    photo: str | None = None
    active: bool | None = None
    cafe_ids: list[int] | None = None


class DishOut(DishBase):
    """
    Схема вывода блюда.

    Содержит идентификатор, активность и список связанных кафе.
    """
    model_config = ConfigDict(from_attributes=True)
    id: int
    active: bool
    cafe_ids: list[int] = Field(default_factory=list)


class DishList(BaseModel):
    """
    Схема для пагинированного списка блюд.

    Используется в эндпоинтах list_dishes и list_active_dishes.
    """
    model_config = ConfigDict(from_attributes=True)
    total: int
    items: list[DishOut]
