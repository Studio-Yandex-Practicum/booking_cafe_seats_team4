from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .user import UserShortInfo


class CafeBase(BaseModel):
    """Базовая схема Кафе."""

    name: str = Field(..., max_length=200)
    address: str
    phone: str = Field(..., max_length=20)
    description: Optional[str] = None
    photo_id: Optional[UUID] = None


class CafeCreate(CafeBase):
    """Схема создания Кафе."""

    managers_id: List[int]


class CafeUpdate(BaseModel):
    """Схема обновления Кафе."""

    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    photo_id: Optional[UUID] = None
    managers_id: Optional[List[int]] = None
    is_active: Optional[bool] = None


class CafeShortInfo(BaseModel):
    """Краткая информация о Кафе."""

    id: int
    name: str
    address: str
    phone: str
    description: Optional[str] = None
    photo_id: Optional[UUID] = None

    class Config:
        """Конфигурация схемы."""

        orm_mode = True


class CafeInfo(CafeShortInfo):
    """Полная информация о Кафе."""

    managers: List[UserShortInfo]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TableBase(BaseModel):
    """Базовая схема Стола."""

    description: Optional[str] = None
    seat_number: int


class TableCreate(TableBase):
    """Схема создания Стола."""

    cafe_id: int


class TableUpdate(BaseModel):
    """Схема обновления Стола."""

    cafe_id: Optional[int] = None
    description: Optional[str] = None
    seat_number: Optional[int] = None
    is_active: Optional[bool] = None


class TableShortInfo(BaseModel):
    """Краткая информация о Столе."""

    id: int
    description: Optional[str] = None
    seat_number: int

    class Config:
        """Конфигурация схемы."""

        orm_mode = True


class TableInfo(TableShortInfo):
    """Полная информация о Столе."""

    cafe: CafeShortInfo
    is_active: bool
    created_at: datetime
    updated_at: datetime
