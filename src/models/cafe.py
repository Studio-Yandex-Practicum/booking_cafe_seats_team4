from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.cafe_manager import cafe_manager

if TYPE_CHECKING:
    from models.user import User


class Cafe(Base):
    """ORM-модель кафе с названием и менеджерами."""

    __tablename__ = 'cafes'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # связь many-to-many с пользователями-менеджерами
    managers: Mapped[list[User]] = relationship(
        'User',
        secondary=cafe_manager,
        back_populates='managed_cafes',
        lazy='selectin',
    )
