from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel
from .relations import cafe_actions


class Action(BaseModel):
    """Модель акций."""

    __tablename__ = 'actions'

    description = Column(Text, nullable=False)

    # Был FK на media.id - оставила внешний идентификатор онли
    photo_id = Column(UUID(as_uuid=True), nullable=True)

    cafes = relationship(
        'Cafe',
        secondary=cafe_actions,
        back_populates='actions',
        lazy='selectin',
    )
