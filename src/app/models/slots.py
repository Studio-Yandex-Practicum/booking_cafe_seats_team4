from sqlalchemy import Column, ForeignKey, Integer, DateTime

from app.models.base import Base


class Slots(Base):
    cafe_id = Column(Integer, ForeignKey('cafes.id'))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
