from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.models.relations import cafe_actions

if TYPE_CHECKING:
    from src.models.cafe import Cafe


class Action(BaseModel):
    """Модель акции, действующей в одном или нескольких кафе."""

    __tablename__ = 'actions'

    description: Mapped[str] = mapped_column(Text, nullable=False)
    photo_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    cafes: Mapped[list['Cafe']] = relationship(
        'Cafe',
        secondary=cafe_actions,
        back_populates='actions',
        lazy='selectin',
    )
