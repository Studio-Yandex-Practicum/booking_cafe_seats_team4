from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from core.constants import DESCRIPTION_MIN, NAME_MAX, NAME_MIN

from .cafe import CafeShortInfo


class DishBase(BaseModel):
    """Базовая схема блюда."""

    name: str = Field(
        ...,
        min_length=NAME_MIN,
        max_length=NAME_MAX, description="Название блюда",
    )
    description: str = Field(
        ...,
        min_length=DESCRIPTION_MIN,
        description="Описание блюда",
    )
    photo_id: UUID = Field(..., description="UUID фото блюда")
    price: float = Field(..., gt=0, description="Цена блюда")


class DishCreate(DishBase):
    """Создание блюда."""

    cafes_id: List[int] = Field(
        ...,
        min_items=1,
        description="Список ID кафе, где доступно блюдо",
    )


class DishUpdate(BaseModel):
    """Частичное обновление блюда."""

    name: Optional[str] = Field(
        None,
        min_length=NAME_MIN,
        max_length=NAME_MAX,
        description="Название блюда",
    )
    description: Optional[str] = Field(
        None,
        min_length=DESCRIPTION_MIN,
        description="Описание блюда",
    )
    photo_id: Optional[UUID] = Field(None, description="UUID фото блюда")
    price: Optional[float] = Field(None, gt=0, description="Цена блюда")
    cafes_id: Optional[List[int]] = Field(
        None, min_items=1,
        description="Список ID кафе",
    )
    is_active: Optional[bool] = Field(None, description="Активно ли блюдо")


class DishInfo(DishBase):
    """Информация о блюде."""

    id: int = Field(..., description="ID блюда")
    cafes: List[CafeShortInfo] = Field(
        ...,
        description="Кафе, где доступно блюдо",
    )
    is_active: bool = Field(..., description="Активно ли блюдо")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")

    model_config = ConfigDict(from_attributes=True)
