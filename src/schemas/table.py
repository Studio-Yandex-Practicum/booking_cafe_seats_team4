from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .cafe import CafeShortInfo


class TableBase(BaseModel):
    """Базовая схема Стола."""

    description: str
    seat_number: int = Field(..., gt=0)


class TableCreate(TableBase):
    """Схема создания Стола."""

    cafe_id: int


class TableUpdate(BaseModel):
    """Схема обновления Стола."""

    cafe_id: Optional[int] = None
    description: Optional[str] = None
    seat_number: Optional[int] = None
    is_active: Optional[bool] = None


class TableShortInfo(TableBase):
    """Краткая информация о Столе."""

    id: int

    model_config = {'from_attributes': True}


class TableInfo(TableShortInfo):
    """Полная информация о Столе."""

    cafe: CafeShortInfo
    is_active: bool
    created_at: datetime
    updated_at: datetime
