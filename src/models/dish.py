from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Numeric,
    String,
    Text,
    Column,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import BaseModel

from .relations import cafe_dishes, booking_dishes


class Dish(BaseModel):
    """Модель блюда в меню кафе."""

    __tablename__ = "dishes"

    cafe_id = Column(
        Integer,
        ForeignKey('cafes.id', ondelete='CASCADE'),
        nullable=False
    )
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)

    is_available = Column(Boolean, default=True, nullable=False)
    media_id = Column(UUID(as_uuid=True), nullable=True)

    cafes = relationship(
        'Cafe',
        secondary=cafe_dishes,
        back_populates='dishes',
    )
    bookings = relationship(
        'Booking',
        secondary=booking_dishes,
        back_populates='dishes',
    )
