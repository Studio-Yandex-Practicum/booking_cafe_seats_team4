from __future__ import annotations

from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from .cafe import CafeShortInfo

TableDescriptionStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]

PositiveInt = Annotated[int, Field(gt=0)]


class TableCreate(BaseModel):
    """Схема создания Стола."""

    description: TableDescriptionStr
    seat_number: PositiveInt


class TableUpdate(BaseModel):
    """Схема обновления Стола."""

    description: Optional[TableDescriptionStr] = None
    seat_number: Optional[PositiveInt] = None
    is_active: Optional[bool] = None


class TableShortInfo(BaseModel):
    """Краткая информация о Столе."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    seat_number: int


class TableInfo(TableShortInfo):
    """Полная информация о Столе."""

    cafe: CafeShortInfo
    is_active: bool
    created_at: datetime
    updated_at: datetime
