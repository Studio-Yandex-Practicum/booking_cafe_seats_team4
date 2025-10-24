from __future__ import annotations

from datetime import date, datetime
from enum import IntEnum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.constants import BOOKING_NOTE_MAX
from schemas.cafe import CafeShortInfo
from schemas.user import UserShortInfo

from .slots import TimeSlotShortInfo  # noqa
from .table import TableShortInfo  # noqa
from .validators import validate_date_not_past, validate_positive_number


class BookingStatus(IntEnum):
    """Статусы бронирования."""

    ACTIVE = 0
    CANCELLED = 1
    COMPLETED = 2


class BookingBase(BaseModel):
    """Базовая схема бронирования."""

    cafe_id: int
    tables_id: List[int]
    slots_id: List[int]
    guest_number: int
    note: Optional[str] = Field(None, max_length=BOOKING_NOTE_MAX)
    status: BookingStatus
    booking_date: date = Field(..., description="Дата в формате YYYY-MM-DD")

    @field_validator('booking_date')
    @classmethod
    def _validate_booking_date_not_in_past(cls, v: date) -> date:
        return validate_date_not_past(v)

    @field_validator('guest_number')
    @classmethod
    def _validate_guest_number_positive(cls, v: int) -> int:
        return validate_positive_number(v, 'Количество гостей')

    @field_validator('note')
    @classmethod
    def _validate_note_length(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > BOOKING_NOTE_MAX:
            raise ValueError(
                f'Длина заметки не может превышать '
                f'{BOOKING_NOTE_MAX} символов',
            )
        return v


class BookingCreate(BookingBase):
    """Схема для создания бронирования."""


class BookingUpdate(BaseModel):
    """Схема для обновления бронирования."""

    cafe_id: Optional[int] = None
    tables_id: Optional[List[int]] = None
    slots_id: Optional[List[int]] = None
    guest_number: Optional[int] = None
    booking_date: Optional[date] = Field(
        None, description="Дата в формате YYYY-MM-DD",
    )
    status: Optional[BookingStatus] = None
    note: Optional[str] = Field(None, max_length=BOOKING_NOTE_MAX)
    is_active: Optional[bool] = None

    @field_validator('booking_date')
    @classmethod
    def _validate_booking_date_not_in_past_optional(
        cls,
        v: Optional[date],
    ) -> Optional[date]:
        if v is not None:
            return validate_date_not_past(v)
        return v

    @field_validator('booking_date')
    @classmethod
    def _validate_booking_date_format_optional(
        cls,
        v: Optional[date],
    ) -> Optional[date]:
        """Проверяет, что дата соответствует формату YYYY-MM-DD."""
        if v is not None and not isinstance(v, date):
            raise ValueError('Дата должна быть в формате YYYY-MM-DD')
        return v

    @field_validator('guest_number')
    @classmethod
    def _validate_guest_number_positive_optional(
        cls,
        v: Optional[int],
    ) -> Optional[int]:
        if v is not None:
            return validate_positive_number(v, 'Количество гостей')
        return v

    @field_validator('note')
    @classmethod
    def _validate_note_length_optional(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > BOOKING_NOTE_MAX:
            raise ValueError(
                f'Длина заметки не может превышать '
                f'{BOOKING_NOTE_MAX} символов',
            )
        return v


class BookingShortInfo(BaseModel):
    """Краткая информация о бронировании."""

    user_id: int
    id: int
    booking_date: date = Field(..., description="Дата в формате YYYY-MM-DD")
    status: BookingStatus

    model_config = ConfigDict(from_attributes=True)


class BookingInfo(BookingShortInfo):
    """Полная информация о бронировании."""

    user: UserShortInfo
    cafe: CafeShortInfo
    tables: List[TableShortInfo] = Field(alias='tables_id')
    slots: List[TimeSlotShortInfo] = Field(alias='slots_id')
    guest_number: int
    note: Optional[str] = Field(None, max_length=BOOKING_NOTE_MAX)
    is_active: bool
    created_at: datetime
    updated_at: datetime
