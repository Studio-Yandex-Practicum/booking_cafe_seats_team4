from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import BaseModel
from .relations import booking_slots


class Slot(BaseModel):
    """Модель слотов."""

    __tablename__ = 'slots'

    cafe_id = Column(Integer, ForeignKey('cafes.id'), nullable=False)
    start_time = Column(String(5), nullable=False)
    end_time = Column(String(5), nullable=False)
    description = Column(Text, nullable=False)

    cafe = relationship('Cafe', back_populates='slots')
    bookings = relationship(
        'Booking',
        secondary=booking_slots,
        back_populates='slots',
    )
