from sqlalchemy import Column, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from models.base import BaseModel


class Action(BaseModel):
    """Модель акций."""
    __tablename__ = 'actions'

    description = Column(Text, nullable=False)
    photo_id = Column(
        UUID(as_uuid=True),
        ForeignKey('media.id'),
        nullable=True)

    cafes = relationship(
        'Cafe',
        secondary='cafe_actions',
        back_populates='actions',
    )
