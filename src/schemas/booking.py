from datetime import date, datetime
from enum import IntEnum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from .cafe import TableShortInfo  # noqa
from .slots import TimeSlotShortInfo  # noqa
from .validators import validate_date_not_past, validate_positive_number


class BookingStatus(IntEnum):
    """Статусы бронирования."""

    ACTIVE = 0
    CANCELLED = 1
    COMPLETED = 2


class BookingBase(BaseModel):
    """Базовая схема бронирования."""

    user_id: int
    cafe_id: int
    tables_id: List[int]
    slots_id: List[int]
    guest_number: int
    note: Optional[str] = None
    status: BookingStatus
    booking_date: date

    @field_validator('booking_date')
    @classmethod
    def _validate_booking_date_not_in_past(cls, v: date) -> date:
        return validate_date_not_past(v)

    @field_validator('guest_number')
    @classmethod
    def _validate_guest_number_positive(cls, v: int) -> int:
        return validate_positive_number(v, 'Количество гостей')


class BookingCreate(BookingBase):
    """Схема для создания бронирования."""

    pass


class BookingUpdate(BaseModel):
    """Схема для обновления бронирования."""

    cafe_id: Optional[int] = None
    tables_id: Optional[List[int]] = None
    slots_id: Optional[List[int]] = None
    guest_number: Optional[int] = None
    booking_date: Optional[date] = None
    status: Optional[BookingStatus] = None
    note: Optional[str] = None
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

    @field_validator('guest_number')
    @classmethod
    def _validate_guest_number_positive_optional(
        cls,
        v: Optional[int],
    ) -> Optional[int]:
        if v is not None:
            return validate_positive_number(v, 'Количество гостей')
        return v


class BookingShortInfo(BaseModel):
    """Краткая информация о бронировании."""

    id: int
    booking_date: date
    status: BookingStatus
    model_config = ConfigDict(from_attributes=True)


class BookingInfo(BookingShortInfo):
    """Полная информация о бронировании."""

    user_id: int
    cafe_id: int
    tables: List['TableShortInfo']
    slots: List['TimeSlotShortInfo']
    guest_number: int
    note: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
