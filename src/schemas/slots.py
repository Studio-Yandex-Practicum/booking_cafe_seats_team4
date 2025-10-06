from typing import Optional
from datetime import datetime

from pydantic import BaseModel, constr, validator

from validators import validate_time_format, validate_time_range


class TimeSlotBase(BaseModel):
    cafe_id: int
    start_time: constr(min_length=5, max_length=5)
    end_time: constr(min_length=5, max_length=5)
    description: str

    @validator('start_time', 'end_time')
    def validate_time_format(cls, time_value):
        return validate_time_format(time_value)

    @validator('end_time')
    def validate_time_range(cls, end_time, values):
        if 'start_time' in values:
            start_time = values['start_time']
            validate_time_range(start_time, end_time)
        return end_time


class TimeSlotCreate(TimeSlotBase):
    pass


class TimeSlotUpdate(BaseModel):
    cafe_id: Optional[int] = None
    start_time: Optional[constr(min_length=5, max_length=5)] = None
    end_time: Optional[constr(min_length=5, max_length=5)] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    @validator('start_time', 'end_time')
    def validate_time_format(cls, time_value):
        if time_value is not None:
            return validate_time_format(time_value)
        return time_value

    @validator('end_time')
    def validate_time_range(cls, end_time, values):
        start_time = values.get('start_time')
        if start_time is not None and end_time is not None:
            validate_time_range(start_time, end_time)
        return end_time


class TimeSlotShortInfo(BaseModel):
    id: int
    start_time: str
    end_time: str
    description: str

    class Config:
        orm_mode = True


class TimeSlotInfo(TimeSlotShortInfo):
    cafe_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
