from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class ActionBase(BaseModel):
    """Базовая схема акции.

    Общие поля: текстовое описание, optional ID фото и список ID кафе,
    к которым привязана акция.
    """

    description: str
    photo_id: UUID | None = None
    cafes_id: list[int] = Field(default_factory=list)


class ActionCreate(ActionBase):
    """Схема для создания акции. Наследует поля ActionBase."""

    pass


class ActionUpdate(ActionBase):
    """Схема частичного обновления акции.

    Все поля опциональны; если поле не передано, значение не изменяется.
    """

    description: str | None = None
    cafes_id: list[int] | None = None


class ActionInfo(ActionBase):
    """Схема ответа с данными акции.

    Включает служебные поля: ID, флаг активности и метки времени
    создания/обновления. from_attributes=True позволяет собирать объект
    из ORM-модели.
    """

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
