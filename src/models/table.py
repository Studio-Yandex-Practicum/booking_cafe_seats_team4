from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import BaseModel
from .relations import booking_tables


class Table(BaseModel):
    """Модель Стол."""

    __tablename__ = 'tables'

    description = Column(String, nullable=False)
    seat_number = Column(Integer, nullable=False)
    cafe_id = Column(Integer, ForeignKey('cafes.id'), nullable=False)

    cafe = relationship(
        'Cafe',
        back_populates='tables',
        lazy='joined',
    )
    bookings = relationship(
        'Booking',
        secondary=booking_tables,
        back_populates='tables_id',
        lazy='noload',
    )
