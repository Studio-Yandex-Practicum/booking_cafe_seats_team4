from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class ActionCreate(BaseModel):
    """Схема создания акции."""

    description: str
    photo_id: UUID | None = None
    cafe_ids: list[int] = Field(default_factory=list)


class ActionUpdate(BaseModel):
    """Схема частичного обновления акции."""

    description: str | None = None
    photo_id: UUID | None = None
    cafe_ids: list[int] | None = None


class ActionOut(BaseModel):
    """Схема ответа по акции."""

    id: int
    description: str
    photo_id: UUID | None = None
    cafe_ids: list[int]

    model_config = ConfigDict(from_attributes=True)
