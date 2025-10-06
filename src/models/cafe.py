from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from src.core.constants import CAFE_NAME_MAX
from src.models.base import Base
from src.models.cafe_manager import cafe_manager


class Cafe(Base):
    """ORM-модель кафе с названием и менеджерами."""

    __tablename__ = 'cafes'

    id = Column(Integer, primary_key=True)
    name = Column(String(CAFE_NAME_MAX), nullable=False)

    managers = relationship(
        'User',
        secondary=cafe_manager,
        back_populates='managed_cafes',
        lazy='selectin',
    )
