from __future__ import annotations

from datetime import datetime
from typing import Annotated, List, Set
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    StringConstraints,
    field_validator,
)

from core.constants import CAFE_ADDRESS_MAX, CAFE_NAME_MAX, PHONE_MAX
from schemas.user import UserShortInfo

CafeNameStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=2,
        max_length=CAFE_NAME_MAX,
    ),
]

CafeAddressStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=5,
        max_length=CAFE_ADDRESS_MAX,
    ),
]

CafePhoneStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        max_length=PHONE_MAX,
    ),
]

CafeDescriptionStr = Annotated[str, StringConstraints(strip_whitespace=True)]


class CafeCreate(BaseModel):
    """Схема для создания нового кафе."""

    name: CafeNameStr
    address: CafeAddressStr
    phone: CafePhoneStr
    description: CafeDescriptionStr | None = None
    photo_id: UUID | None = None
    managers_id: Set[int] | None = None

    @field_validator('description', mode='before')
    @classmethod
    def empty_str_to_none(cls, v: str | None) -> str | None:
        """Преобразует пустую строку в None."""
        if isinstance(v, str) and not v.strip():
            return None
        return v

    model_config = ConfigDict(
        json_schema_extra={
            'example': {
                'name': "Кофейня 'Уют'",
                'address': 'г. Санкт-Петербург, Невский пр., д. 28',
                'phone': '+7(812)555-35-35',
                'description': 'Лучший кофе и свежая выпечка в центре города.',
                'photo_id': '123e4567-e89b-12d3-a456-426614174000',
                'managers_id': [10, 15],
            },
        },
    )


class CafeUpdate(BaseModel):
    """Схема для частичного обновления кафе."""

    name: CafeNameStr | None = None
    address: CafeAddressStr | None = None
    phone: CafePhoneStr | None = None
    description: CafeDescriptionStr | None = None
    is_active: bool | None = None
    photo_id: UUID | None = None
    managers_id: Set[int] | None = None

    @field_validator('description', mode='before')
    @classmethod
    def empty_str_to_none(cls, v: str | None) -> str | None:
        """Преобразует пустую строку в None."""
        if isinstance(v, str) and not v.strip():
            return None
        return v


class CafeShortInfo(BaseModel):
    """Краткая информация о кафе (для вложенных представлений)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    phone: str
    description: str | None
    photo_id: UUID | None


class CafeInfo(CafeShortInfo):
    """Полная информация о кафе для ответа API."""

    is_active: bool
    created_at: datetime
    updated_at: datetime
    managers: List[UserShortInfo] = []
