from sqlalchemy import Column, Integer, Table, UniqueConstraint

from models.base import Base

# временная таблица-связка без внешних ключей
cafe_manager = Table(
    'cafe_manager',
    Base.metadata,
    Column('cafe_id', Integer, primary_key=True),
    Column('user_id', Integer, primary_key=True),
    UniqueConstraint('cafe_id', 'user_id', name='uq_cafe_manager_cafe_user'),
)
