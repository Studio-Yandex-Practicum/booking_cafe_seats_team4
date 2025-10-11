from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Table,
    Text,
    Uuid,
)
from sqlalchemy.orm import relationship

from src.db.base import Base


# Ассоциация блюд и кафе (многие-ко-многим)
dish_cafe = Table(
    "dish_cafe",
    Base.metadata,
    Column("dish_id", Uuid(as_uuid=True),
           ForeignKey("dishes.id", ondelete="CASCADE"),
           primary_key=True),
    Column("cafe_id", Uuid(as_uuid=True),
           ForeignKey("cafes.id", ondelete="CASCADE"),
           primary_key=True),
)


class Dish(Base):
    """
    Модель блюда.

    Описывает блюдо, предлагаемое в одном или нескольких кафе.
    Содержит базовые поля: название, описание, цену, фото и признак активности.
    Между Dish и Cafe реализована связь многие-ко-многим
    через таблицу dish_cafe.
    """

    __tablename__ = "dishes"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    photo = Column(String(255), nullable=True)

    active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True),
                        nullable=False,
                        default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    cafes = relationship(
        "Cafe",
        secondary=dish_cafe,
        back_populates="dishes",
        lazy="selectin",
    )
