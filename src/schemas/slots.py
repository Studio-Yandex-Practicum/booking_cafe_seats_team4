from datetime import datetime
from typing import Annotated, Optional, Self  # <-- добавили Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from .validators import validate_time_format, validate_time_range

TimeStr = Annotated[str, Field(min_length=5, max_length=5)]


class TimeSlotBase(BaseModel):
    """Базовая схема временного слота."""

    cafe_id: int
    start_time: TimeStr  # 'HH:MM'
    end_time: TimeStr  # 'HH:MM'
    description: str

    # формат времени для каждого поля
    @field_validator('start_time', 'end_time')
    @classmethod
    def _validate_time_format(cls, v: str) -> str:
        return validate_time_format(v)

    # корректность диапазона (нужны оба поля)
    @model_validator(mode='after')
    def _validate_time_range(self) -> Self:  # <-- аннотация возврата
        validate_time_range(self.start_time, self.end_time)
        return self


class TimeSlotCreate(TimeSlotBase):
    """Схема для создания временного слота."""

    pass


class TimeSlotUpdate(BaseModel):
    """Схема для обновления временного слота."""

    cafe_id: Optional[int] = None
    start_time: Optional[TimeStr] = None
    end_time: Optional[TimeStr] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator('start_time', 'end_time')
    @classmethod
    def _validate_time_format_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_time_format(v)

    @model_validator(mode='after')
    def _validate_time_range_optional(self) -> Self:  # <-- аннотация возврата
        if self.start_time is not None and self.end_time is not None:
            validate_time_range(self.start_time, self.end_time)
        return self


class TimeSlotShortInfo(BaseModel):
    """Краткая информация о временном слоте."""

    id: int
    start_time: str
    end_time: str
    description: str

    # pydantic v2
    model_config = ConfigDict(from_attributes=True)


class TimeSlotInfo(TimeSlotShortInfo):
    """Полная информация о временном слоте."""

    cafe_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
