from uuid import UUID

from pydantic import BaseModel


class MediaUploadResponse(BaseModel):
    """Схема ответа при загрузке изображения."""

    media_id: UUID
