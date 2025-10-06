from sqlalchemy import Column, ForeignKey, Integer, Table

from src.core.db import Base

cafe_managers = Table(
    'cafe_managers',
    Base.metadata,
    Column('cafe_id', Integer, ForeignKey('cafes.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
)

cafe_dishes = Table(
    'cafe_dishes',
    Base.metadata,
    Column('cafe_id', Integer, ForeignKey('cafes.id'), primary_key=True),
    Column('dish_id', Integer, ForeignKey('dishes.id'), primary_key=True),
)

cafe_actions = Table(
    'cafe_actions',
    Base.metadata,
    Column('cafe_id', Integer, ForeignKey('cafes.id'), primary_key=True),
    Column('action_id', Integer, ForeignKey('actions.id'), primary_key=True),
)

booking_dishes = Table(
    'booking_dishes',
    Base.metadata,
    Column('booking_id', Integer, ForeignKey('bookings.id'), primary_key=True),
    Column('dish_id', Integer, ForeignKey('dishes.id'), primary_key=True),
)

booking_tables = Table(
    'booking_tables',
    Base.metadata,
    Column('booking_id', Integer, ForeignKey('bookings.id'), primary_key=True),
    Column('table_id', Integer, ForeignKey('tables.id'), primary_key=True),
)

booking_slots = Table(
    'booking_slots',
    Base.metadata,
    Column('booking_id', Integer, ForeignKey('bookings.id'), primary_key=True),
    Column('slot_id', Integer, ForeignKey('slots.id'), primary_key=True),
)