from __future__ import annotations
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from src.models.base import BaseModel
from src.models.relations import cafe_dishes, booking_dishes

if TYPE_CHECKING:
    from src.models.cafe import Cafe
    from src.models.booking import Booking


class Dish(BaseModel):
    """Модель блюда меню кафе."""

    __tablename__ = "dishes"

    # ▶ Основные поля
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True,
                                               nullable=False)
    media_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True),
                                                  nullable=True)
    # ▶ active — унаследовано из BaseModel

    # ▶ Связи
    cafes: Mapped[list["Cafe"]] = relationship(
        "Cafe",
        secondary=cafe_dishes,
        back_populates="dishes",
        lazy="selectin",
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        secondary=booking_dishes,
        back_populates="dishes",
        lazy="selectin",
    )
