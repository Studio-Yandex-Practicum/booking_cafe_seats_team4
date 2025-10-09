from __future__ import annotations

from sqlalchemy import Boolean, Column, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .relations import booking_dishes, cafe_dishes
from src.models.base import BaseModel


class Dish(BaseModel):
    """Модель блюда в меню кафе.
    ТЗ: блюдо может быть в нескольких кафе → many-to-many через cafe_dishes.
    В BaseModel ожидаются: id (UUID/int), created_at, updated_at, active.
    """

    __tablename__ = 'dishes'

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)

    # Текущая доступность блюда в меню (отдельно от "active" из BaseModel)
    is_available = Column(Boolean, default=True, nullable=False)

    # ID изображения (UUID4) из сервиса /media
    media_id = Column(UUID(as_uuid=True), nullable=True)

    # Связь с кафе (M2M по ТЗ)
    cafes = relationship(
        'Cafe',
        secondary=cafe_dishes,
        back_populates='dishes',
        lazy='selectin',
    )

    # Предзаказ блюд в составе бронирования (опционально по ТЗ)
    bookings = relationship(
        'Booking',
        secondary=booking_dishes,
        back_populates='dishes',
        lazy='selectin',
    )
