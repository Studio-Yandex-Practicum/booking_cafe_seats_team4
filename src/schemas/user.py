from datetime import datetime
from enum import IntEnum
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    field_validator,
    model_validator,
)


class UserRole(IntEnum):
    """Роль пользователя."""

    USER = 0
    MANAGER = 1
    ADMIN = 2


class UserCreate(BaseModel):
    """Схема создания пользователя."""

    username: str
    # хотя бы одно из двух (валидируем ниже)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    tg_id: Optional[str] = None
    password: str

    # Зарещаем пустых строк для контактов и tg_id.
    @field_validator('email', 'phone', 'tg_id', mode='before')
    @classmethod
    def _no_blank(cls, v: object) -> object:
        if isinstance(v, str) and v.strip() == '':
            raise ValueError('Поле не должно быть пустой строкой.')
        return v

    # Запрашиваем хотя бы один контакт.
    @model_validator(mode='after')
    def _require_contact(self) -> 'UserCreate':
        if not (self.email or self.phone):
            raise ValueError('Нужно указать email или phone (хотя бы одно).')
        return self


class UserShortInfo(BaseModel):
    """Короткая информация о пользователе."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    tg_id: Optional[str] = None


class UserInfo(BaseModel):
    """Полная информация о пользователе."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    tg_id: Optional[str] = None
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

    # Запрещаем  null в частичном апдейте (по ТЗ).
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
    def forbid_nulls(cls, v: object) -> object:
        """Валидация, что не null."""
        if v is None:
            raise ValueError('null is not allowed for this field')
        return v

    # Плюс запрешаем пустые строки в апдейте.
    @field_validator(
        'username',
        'email',
        'phone',
        'tg_id',
        'password',
        mode='before',
    )
    @classmethod
    def _no_blank(cls, v: object) -> object:
        if isinstance(v, str) and v.strip() == '':
            raise ValueError('Пустые строки не допускаются.')
        return v
