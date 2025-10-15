from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel
from .relations import booking_dishes, cafe_dishes


class Dish(BaseModel):
    """Модель блюда в меню кафе."""

    __tablename__ = 'dishes'

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=False)
    photo_id = Column(UUID(as_uuid=True), nullable=False)

    cafes = relationship(
        'Cafe',
        secondary=cafe_dishes,
        back_populates='dishes',
        lazy='selectin',
    )
    bookings = relationship(
        'Booking',
        secondary=booking_dishes,
        back_populates='dishes',
        lazy='selectin',
    )
