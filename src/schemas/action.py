from uuid import UUID
from pydantic import BaseModel


class ActionCreate(BaseModel):
    description: str
    photo_id: UUID | None = None
    cafe_ids: list[int] = []  # к каким кафе привязать


class ActionUpdate(BaseModel):
    description: str | None = None
    photo_id: UUID | None = None
    cafe_ids: list[int] | None = None


class ActionOut(BaseModel):
    id: int
    description: str
    photo_id: UUID | None = None
    cafe_ids: list[int]

    class Config:
        from_attributes = True
