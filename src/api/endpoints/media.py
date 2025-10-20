import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from api.deps import require_manager_or_admin
from api.validators.media import (
    check_len_file,
    check_media_id,
    media_allowed_content_type,
    media_exist,
)
from celery_tasks.tasks import save_image
from core.config import settings
from models.user import User
from schemas.media import MediaUploadResponse

router = APIRouter(prefix='/media', tags=['media'])

MEDIA_PATH = Path(settings.MEDIA_PATH)


@router.post('', response_model=MediaUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(require_manager_or_admin),
) -> MediaUploadResponse:
    """Эндпоинт загрузки изображений."""
    file = await media_allowed_content_type(file)
    contents = await check_len_file(file)
    media_id = str(uuid.uuid4())
    try:
        save_image.delay(contents, media_id)
        return {
            'media_id': media_id,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Ошибка при обработке изображения: {str(e)}',
        )


@router.get('/{media_id}')
async def get_image(media_id: str) -> FileResponse:
    """Получение изображения по ID."""
    media_id = check_media_id(media_id)
    filename = f'{media_id}.jpg'
    file_path = MEDIA_PATH / filename
    file_path = media_exist(file_path)
    return FileResponse(
        path=file_path,
        media_type='image/jpeg',
        filename=f'{media_id}.jpg',
    )
