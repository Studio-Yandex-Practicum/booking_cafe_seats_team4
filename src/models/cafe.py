from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel
from .relations import cafe_actions, cafe_dishes, cafe_managers


class Cafe(BaseModel):
    """Модель Кафе."""

    __tablename__ = 'cafes'

    name = Column(String(200), nullable=False)
    address = Column(String(300), nullable=False)
    phone = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)

    # Был ForeignKey('media.id') + relationship('Media')
    # Стало: внешний ИД объекта, который хранится вне нашей БД
    photo_id = Column(UUID(as_uuid=True), nullable=True)

    tables = relationship(
        'Table',
        back_populates='cafe',
        cascade='all, delete-orphan',
        lazy='selectin',
    )
    slots = relationship(
        'Slot',
        back_populates='cafe',
        cascade='all, delete-orphan',
        lazy='selectin',
    )
    bookings = relationship(
        'Booking',
        back_populates='cafe',
        lazy='selectin',
    )
    managers = relationship(
        'User',
        secondary=cafe_managers,
        back_populates='managed_cafes',
        lazy='selectin',
    )
    dishes = relationship(
        'Dish',
        secondary=cafe_dishes,
        back_populates='cafes',
        lazy='selectin',
    )
    actions = relationship(
        'Action',
        secondary=cafe_actions,
        back_populates='cafes',
        lazy='selectin',
    )
