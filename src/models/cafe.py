from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from .base import BaseModel
from .relations import booking_tables, cafe_actions, cafe_dishes, cafe_managers


class Cafe(BaseModel):
    """Модель Кафе."""

    __tablename__ = 'cafes'

    name = Column(String(200), nullable=False)
    address = Column(String, nullable=False)
    phone = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    photo_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('media.id'),
        nullable=True,
    )

    photo = relationship('Media')
    tables = relationship(
        'Table',
        back_populates='cafe',
        cascade='all, delete-orphan',
    )
    slots = relationship(
        'Slot',
        back_populates='cafe',
        cascade='all, delete-orphan',
    )
    managers = relationship(
        'User',
        secondary=cafe_managers,
        back_populates='managed_cafes',
    )
    actions = relationship(
        'Action',
        secondary=cafe_actions,
        back_populates='cafes',
    )
    dishes = relationship(
        'Dish',
        secondary=cafe_dishes,
        back_populates='cafes',
    )
    bookings = relationship('Booking', back_populates='cafe')


class Table(BaseModel):
    """Модель Стол."""

    __tablename__ = 'tables'

    cafe_id = Column(Integer, ForeignKey('cafes.id'), nullable=False)
    description = Column(String, nullable=True)
    seat_number = Column(Integer, nullable=False)

    cafe = relationship('Cafe', back_populates='tables')
    bookings = relationship(
        'Booking',
        secondary=booking_tables,
        back_populates='tables',
    )
