from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from core.constants import DESCRIPTION_MIN, NAME_MAX, NAME_MIN
from .cafe import CafeShortInfo


class DishBase(BaseModel):
    """Базовая схема блюда."""

    name: str = Field(..., min_length=NAME_MIN, max_length=NAME_MAX)
    description: str = Field(..., min_length=DESCRIPTION_MIN)
    photo_id: UUID
    price: int


class DishCreate(DishBase):
    """Создание блюда."""
    cafes_id: List[int]


class DishInfo(DishBase):
    """Информация о блюде."""

    id: int
    cafes: List[CafeShortInfo]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DishUpdate(BaseModel):
    """Частичное обновление блюда."""

    name: Optional[str] = Field(None, min_length=NAME_MIN, max_length=NAME_MAX)
    description: Optional[str] = Field(None, min_length=DESCRIPTION_MIN)
    photo_id: Optional[UUID]
    price: Optional[int]
    cafes_id: Optional[List[int]]
    is_active: Optional[bool]
