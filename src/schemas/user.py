from datetime import datetime
from enum import IntEnum
from typing import Annotated, Optional

from pydantic import (BaseModel, ConfigDict, EmailStr, Field,
                      StringConstraints, field_validator)

from core.constants import EMAIL_MAX, PHONE_MAX, TG_ID_MAX, USERNAME_MAX

UsernameStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=USERNAME_MAX),
]
PhoneStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=PHONE_MAX),
]
TgIdStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=TG_ID_MAX),
]


class UserRole(IntEnum):
    """Роль пользователя."""

    USER = 0
    MANAGER = 1
    ADMIN = 2


class UserCreate(BaseModel):
    """Модель для регистрации нового пользователя."""

    username: UsernameStr
    password: str
    email: Optional[EmailStr] = Field(default=None, max_length=EMAIL_MAX)
    phone: Optional[PhoneStr] = None
    tg_id: Optional[TgIdStr] = None

    @field_validator('email', 'phone', 'tg_id', mode='before')
    @classmethod
    def _empty_to_none(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None

    @field_validator('password')
    @classmethod
    def _password_create_not_blank(cls, v: str) -> str:
        v = (v or '').strip()
        if not v:
            raise ValueError('Пароль не может быть пустым')
        if len(v) < 6:
            raise ValueError('Минимальная длина пароля — 6 символов')
        return v


class UserShortInfo(BaseModel):
    """Сокращённая информация о пользователе."""

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
    """Модель для частичного обновления пользователя."""

    username: Optional[UsernameStr] = None
    email: Optional[EmailStr] = Field(default=None, max_length=EMAIL_MAX)
    phone: Optional[PhoneStr] = None
    tg_id: Optional[TgIdStr] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None

    @field_validator('email', 'phone', 'tg_id', mode='before')
    @classmethod
    def _empty_to_none(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None

    @field_validator('username')
    @classmethod
    def _username_not_blank(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not v.strip():
            raise ValueError('Имя пользователя не может быть пустым')
        return v

    @field_validator('password')
    @classmethod
    def _password_not_blank(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError('Пароль не может быть пустым')
        if len(v) < 6:
            raise ValueError('Минимальная длина пароля — 6 символов')
        return v
