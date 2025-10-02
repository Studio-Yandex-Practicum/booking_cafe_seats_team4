from datetime import datetime
from enum import IntEnum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class UserRole(IntEnum):
    """Роль пользователя."""

    USER = 0
    MANAGER = 1
    ADMIN = 2


class UserCreate(BaseModel):
    """Схема создания пользователя."""

    username: str
    email: EmailStr
    phone: str
    tg_id: str
    password: str


class UserShortInfo(BaseModel):
    """Короткая информация о пользователе."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: EmailStr
    phone: str
    tg_id: str


class UserInfo(BaseModel):
    """Полная информация о пользователе."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: EmailStr
    phone: str
    tg_id: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    """Частичное обновление пользователя (null запрещён)."""

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    tg_id: Optional[str] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None


@field_validator(
    'username',
    'email',
    'phone',
    'tg_id',
    'role',
    'password',
    mode='before',
)
@classmethod
def forbid_nulls(cls: type['UserUpdate'], v: object) -> object:
    """Запретить явный null/None в полях partial-update."""
    if v is None:
        raise ValueError('null is not allowed for this field')
    return v
