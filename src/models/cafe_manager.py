from sqlalchemy import Column, ForeignKey, Integer, Table

from src.models.base import Base

cafe_manager = Table(
    'cafe_manager',
    Base.metadata,
    Column(
        'cafe_id',
        Integer,
        ForeignKey('cafes.id', ondelete='CASCADE'),
        primary_key=True,
    ),
    Column(
        'user_id',
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        primary_key=True,
    ),
)
