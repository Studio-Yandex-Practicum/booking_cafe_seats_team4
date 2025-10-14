from pydantic import BaseModel
from uuid import UUID


class MediaUploadResponse(BaseModel):
    """Схема ответа при загрузке изображения"""
    media_id: UUID
