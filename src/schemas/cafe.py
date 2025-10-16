from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .user import UserShortInfo


class CafeBase(BaseModel):
    """Базовая схема Кафе."""

    name: str = Field(
        ...,
        max_length=200,
        description='Название кафе',
        example='Кофемания',
    )
    address: str = Field(
        ...,
        max_length=300,
        description='Адрес кафе',
        example='г. Москва, ул. Ленина, д. 1',
    )
    phone: str = Field(
        ...,
        max_length=20,
        description='Контактный телефон',
        example='+7 (999) 123-45-67',
    )
    description: str = Field(
        ...,
        description='Подробное описание кафе',
        example='Уютное место с авторскими десертами и свежеобжаренным кофе.',
    )
    photo_id: UUID = Field(
        ...,
        description='ID фотографии из медиа-хранилища',
        example='f47ac10b-58cc-4372-a567-0e02b2c3d479',
    )


class CafeCreate(CafeBase):
    """Схема создания Кафе."""

    managers_id: List[int] = Field(..., description='Список ID менеджеров')


class CafeUpdate(BaseModel):
    """Схема обновления Кафе."""

    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    photo_id: Optional[UUID] = None
    managers_id: Optional[List[int]] = None
    is_active: Optional[bool] = None


class CafeShortInfo(CafeBase):
    """Краткая информация о Кафе."""

    id: int
    name: str
    address: str
    phone: str
    description: str
    photo_id: UUID

    model_config = {
        'from_attributes': True,  # <- Pydantic 2, заменяет orm_mode
    }


class CafeInfo(CafeShortInfo):
    """Полная информация о Кафе."""

    managers: List[UserShortInfo]
    is_active: bool
    created_at: datetime
    updated_at: datetime
