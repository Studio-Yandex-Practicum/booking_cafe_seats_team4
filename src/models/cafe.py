from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from .base import Base, BaseMixin
from .relations import cafe_manager, action_cafe, dish_cafe, booking_table


class Cafe(Base, BaseMixin):
    name = Column(String(200), nullable=False)
    address = Column(String, nullable=False)
    phone = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    photo_id = Column(PG_UUID(as_uuid=True),
                      ForeignKey('media.id'), nullable=True)

    photo = relationship('Media')
    tables = relationship('Table', back_populates='cafe',
                          cascade='all, delete-orphan')
    slots = relationship('Slot', back_populates='cafe',
                         cascade='all, delete-orphan')
    managers = relationship(
        'User', secondary=cafe_manager,
        # back_populates='managed_cafes' # Если добавим в User
    )
    actions = relationship(
        'Action', secondary=action_cafe, back_populates='cafes'
    )
    dishes = relationship(
        'Dish', secondary=dish_cafe, back_populates='cafes'
    )
    bookings = relationship('Booking', back_populates='cafe')


class Table(Base, BaseMixin):
    cafe_id = Column(Integer, ForeignKey('cafes.id'), nullable=False)
    description = Column(String, nullable=True)
    seat_number = Column(Integer, nullable=False)

    cafe = relationship('Cafe', back_populates='tables')
    bookings = relationship(
        'Booking', secondary=booking_table, back_populates='tables'
    )


class Slot(Base, BaseMixin):
    pass
