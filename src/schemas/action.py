from __future__ import annotations
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class ActionBase(BaseModel):
    """Базовая схема акции."""
    description: str
    photo_id: UUID | None = None
    active: bool = True


class ActionCreate(ActionBase):
    """Схема создания акции."""
    cafe_ids: list[int] = Field(default_factory=list,
                                description="Кафе, где действует акция")


class ActionUpdate(BaseModel):
    """Схема частичного обновления акции."""
    description: str | None = None
    photo_id: UUID | None = None
    active: bool | None = None
    cafe_ids: list[int] | None = Field(None,
                                       description="Полная замена списка кафе")


class ActionOut(ActionBase):
    """Схема вывода акции в ответе API."""
    id: int
    cafe_ids: list[int] = []
    model_config = ConfigDict(from_attributes=True)
