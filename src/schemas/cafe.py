from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .user import UserShortInfo


class CafeBase(BaseModel):
    name: str = Field(..., max_length=200)
    address: str
    phone: str = Field(..., max_length=20)
    description: Optional[str] = None
    photo_id: Optional[UUID] = None


class CafeCreate(CafeBase):
    managers_id: List[int]


class CafeUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    photo_id: Optional[UUID] = None
    managers_id: Optional[List[int]] = None
    is_active: Optional[bool] = None


class CafeShortInfo(BaseModel):
    id: int
    name: str
    address: str
    phone: str
    description: Optional[str] = None
    photo_id: Optional[UUID] = None

    class Config:
        orm_mode = True


class CafeInfo(CafeShortInfo):
    managers: List[UserShortInfo]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TableBase(BaseModel):
    description: Optional[str] = None
    seat_number: int


class TableCreate(TableBase):
    cafe_id: int


class TableUpdate(BaseModel):
    cafe_id: Optional[int] = None
    description: Optional[str] = None
    seat_number: Optional[int] = None
    is_active: Optional[bool] = None


class TableShortInfo(BaseModel):
    id: int
    description: Optional[str] = None
    seat_number: int

    class Config:
        orm_mode = True


class TableInfo(TableShortInfo):
    cafe: CafeShortInfo
    is_active: bool
    created_at: datetime
    updated_at: datetime
