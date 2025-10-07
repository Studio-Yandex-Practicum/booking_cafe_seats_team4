from sqlalchemy import Column, ForeignKey, Integer, Table

from src.core.db import Base


def _t(name: str) -> Table | None:
    return Base.metadata.tables.get(name)


cafe_managers = Table(
    'cafe_managers',
    Base.metadata,
    Column('cafe_id', Integer, ForeignKey('cafes.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
)

# ▶ Акции ↔ Кафе (M2M)
cafe_actions = _t('cafe_actions') or Table(
    'cafe_actions',
    Base.metadata,
    Column('cafe_id', Integer, ForeignKey('cafes.id'), primary_key=True),
    Column('action_id', Integer, ForeignKey('actions.id'), primary_key=True),
    extend_existing=True,  # важен при повторном импорте
)

# ▶ Блюда ↔ Кафе (M2M)
cafe_dishes = _t('cafe_dishes') or Table(
    'cafe_dishes',
    Base.metadata,
    Column('cafe_id', Integer, ForeignKey('cafes.id'), primary_key=True),
    Column('dish_id', Integer, ForeignKey('dishes.id'), primary_key=True),
    extend_existing=True,
)

# ▶ Бронирование ↔ Блюда (для предзаказа; можно ввести позже)
booking_dishes = _t('booking_dishes') or Table(
    'booking_dishes',
    Base.metadata,
    Column('booking_id', Integer, ForeignKey('bookings.id'), primary_key=True),
    Column('dish_id', Integer, ForeignKey('dishes.id'), primary_key=True),
    extend_existing=True,
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
