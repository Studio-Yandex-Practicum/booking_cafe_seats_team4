from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.constants import NAME_MAX

from .base import BaseModel
from .relations import booking_dishes, cafe_dishes


class Dish(BaseModel):
    """Модель блюда в меню кафе."""

    __tablename__ = 'dishes'

    name = Column(String(NAME_MAX), nullable=False)
    description = Column(Text, nullable=True)
    photo_id = Column(UUID(as_uuid=True), nullable=False)
    price = Column(Integer, nullable=False)
    cafe_id = relationship(
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
