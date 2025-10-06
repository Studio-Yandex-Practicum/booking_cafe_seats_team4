from enum import IntEnum

from sqlalchemy import Column, Integer, Text, Date, ForeignKey
from sqlalchemy.orm import relationship

from models.base import BaseModel


class BookingStatus(IntEnum):
    """Статусы бронирования."""
    ACTIVE = 0
    CANCELLED = 1
    COMPLETED = 2


class Booking(BaseModel):
    """Модель резервирования столов."""
    __tablename__ = 'booking'

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    cafe_id = Column(Integer, ForeignKey('cafes.id'), nullable=False)
    guest_number = Column(Integer, nullable=False)
    note = Column(Text, nullable=True)
    status = Column(Integer, nullable=False, default=BookingStatus.ACTIVE)
    booking_date = Column(Date, nullable=False)

    user = relationship('User', back_populates='bookings')
    cafe = relationship('Cafe', back_populates='bookings')
    tables = relationship(
        'Table',
        secondary='booking_tables',
        back_populates='bookings',
    )
    slots = relationship(
        'Slot',
        secondary='booking_slots',
        back_populates='bookings',
    )
    dishes = relationship(
        'Dish',
        secondary='booking_dishes',
        back_populates='bookings',
    )
