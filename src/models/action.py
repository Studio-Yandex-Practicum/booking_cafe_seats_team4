from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.base import BaseModel


class Action(BaseModel):
    __tablename__ = 'actions'

    description = Column(Text, nullable=False)
    photo_id = Column(
        UUID(as_uuid=True),
        ForeignKey('media.id'),
        nullable=True)

    cafes = relationship(
        'Cafe',
        secondary='cafe_actions',
        back_populates='actions'
    )
