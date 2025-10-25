from datetime import datetime
from typing import Annotated, Optional, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    StringConstraints,
    field_validator,
    model_validator,
)
from pydantic import (BaseModel, ConfigDict, Field, StringConstraints,
                      field_validator, model_validator)

from core.constants import DESCRIPTION_MAX, DESCRIPTION_MIN, TIME_LENGTH

from .validators import validate_time_format, validate_time_range

DescriptionStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=DESCRIPTION_MIN,
        max_length=DESCRIPTION_MAX,
    ),
]

TimeStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=TIME_LENGTH,
        max_length=TIME_LENGTH,
        pattern=r'^\d{2}:\d{2}$',
    ),
]


class TimeSlotBase(BaseModel):
    """Базовая схема временного слота БЕЗ cafe_id."""

    start_time: TimeStr
    end_time: TimeStr
    description: DescriptionStr

    @field_validator('start_time', 'end_time')
    @classmethod
    def _validate_time_format(cls, v: str) -> str:
        return validate_time_format(v)

    @model_validator(mode='after')
    def _validate_time_range(self) -> Self:
        validate_time_range(self.start_time, self.end_time)
        return self


class TimeSlotCreate(TimeSlotBase):
    """Схема для создания временного слота БЕЗ cafe_id."""

    pass


class TimeSlotUpdate(BaseModel):
    """Схема для обновления временного слота."""

    start_time: Optional[TimeStr] = None
    end_time: Optional[TimeStr] = None
    description: Optional[DescriptionStr] = None
    is_active: Optional[bool] = None

    @field_validator('start_time', 'end_time')
    @classmethod
    def _validate_time_format_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_time_format(v)

    @model_validator(mode='after')
    def _validate_time_range_optional(self) -> Self:
        if self.start_time is not None and self.end_time is not None:
            validate_time_range(self.start_time, self.end_time)
        return self


class TimeSlotShortInfo(BaseModel):
    """Краткая информация о временном слоте."""

    id: int
    start_time: str
    end_time: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class TimeSlotInfo(TimeSlotShortInfo):
    """Полная информация о временном слоте."""

    cafe_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
