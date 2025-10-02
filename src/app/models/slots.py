from app.models.base import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer


class Slots(Base):
    """Информация о возможных интервалах бронирования."""

    cafe_id = Column(Integer, ForeignKey('cafes.id'))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
