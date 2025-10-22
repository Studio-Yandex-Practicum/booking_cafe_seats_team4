from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class ActionBase(BaseModel):
    description: str
    photo_id: UUID | None = None
    cafes_id: list[int] = Field(default_factory=list)


class ActionCreate(ActionBase):
    pass


class ActionUpdate(ActionBase):
    description: str | None = None
    cafes_id: list[int] | None = None


class ActionInfo(ActionBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
