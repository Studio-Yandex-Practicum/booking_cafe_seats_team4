from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Table,
)
from models.base import Base


# Связь: Кафе <-> Менеджеры (User)
cafe_manager = Table(
    'cafe_manager',
    Base.metadata,
    Column('cafe_id', Integer, ForeignKey('cafes.id'), primary_key=True),
    Column('manager_id', Integer, ForeignKey('users.id'), primary_key=True),
)

# Связь: Бронирование <-> Столы (одна бронь может быть на несколько столов)
booking_table = Table(
    'booking_table',
    Base.metadata,
    Column('booking_id', Integer, ForeignKey('bookings.id'), primary_key=True),
    Column('table_id', Integer, ForeignKey('tables.id'), primary_key=True),
)

# Связь: Бронирование <-> Слоты (бронирование может занимать несколько слотов)
booking_slot = Table(
    'booking_slot',
    Base.metadata,
    Column('booking_id', Integer, ForeignKey('bookings.id'), primary_key=True),
    Column('slot_id', Integer, ForeignKey('slots.id'), primary_key=True),
)

# Связь: Акция <-> Кафе
action_cafe = Table(
    'action_cafe',
    Base.metadata,
    Column('action_id', Integer, ForeignKey('actions.id'), primary_key=True),
    Column('cafe_id', Integer, ForeignKey('cafes.id'), primary_key=True),
)

# Связь: Блюдо <-> Кафе (блюдо может быть в меню нескольких кафе)
dish_cafe = Table(
    'dish_cafe',
    Base.metadata,
    Column('dish_id', Integer, ForeignKey('dishes.id'), primary_key=True),
    Column('cafe_id', Integer, ForeignKey('cafes.id'), primary_key=True),
)
