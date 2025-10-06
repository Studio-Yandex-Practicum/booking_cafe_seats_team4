from typing import Optional, List
from datetime import datetime, date
from enum import IntEnum

from pydantic import BaseModel, validator

from .validators import validate_date_not_past, validate_positive_number
from .tables import TableShortInfo  # noqa
from .slots import TimeSlotShortInfo  # noqa


class BookingStatus(IntEnum):
    """Статусы бронирования."""
    ACTIVE = 0
    CANCELLED = 1
    COMPLETED = 2


class BookingBase(BaseModel):
    user_id: int
    cafe_id: int
    tables_id: List[int]
    slots_id: List[int]
    guest_number: int
    note: Optional[str] = None
    status: BookingStatus
    booking_date: date

    @validator('booking_date')
    def validate_booking_date_not_in_past(cls, booking_date):
        return validate_date_not_past(booking_date)

    @validator('guest_number')
    def validate_guest_number_positive(cls, guest_count):
        return validate_positive_number(guest_count, "Количество гостей")


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

    @validator('booking_date')
    def validate_booking_date_not_in_past(cls, booking_date):
        if booking_date is not None:
            return validate_date_not_past(booking_date)
        return booking_date

    @validator('guest_number')
    def validate_guest_number_positive(cls, guest_count):
        if guest_count is not None:
            return validate_positive_number(guest_count, "Количество гостей")
        return guest_count


class BookingShortInfo(BaseModel):
    """Краткая информация о бронировании."""
    id: int
    booking_date: date
    status: BookingStatus

    class Config:
        orm_mode = True


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

    class Config:
        orm_mode = True
