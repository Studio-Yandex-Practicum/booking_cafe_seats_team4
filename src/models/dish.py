from sqlalchemy import (
    Boolean,
    Column,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel
from .relations import booking_dishes, cafe_dishes


class Dish(BaseModel):
    """Модель блюда."""

    __tablename__ = 'dishes'

    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    photo_id = Column(UUID(as_uuid=True), nullable=True)

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
