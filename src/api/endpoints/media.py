import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from api.deps import require_manager_or_admin
from api.validators.media import check_len_file, media_allowed_content_type
from celery_tasks.tasks import save_image
from core.config import settings
from schemas.media import MediaUploadResponse

router = APIRouter(prefix='/media', tags=['Медиа'])

MEDIA_PATH = Path(settings.MEDIA_PATH)


@router.post(
    '',
    response_model=MediaUploadResponse,
    summary='Загрузка изображений',
    dependencies=[Depends(require_manager_or_admin)],
)
async def upload_image(file: UploadFile = File(...)) -> MediaUploadResponse:
    """Эндпоинт загрузки изображений."""
    file = media_allowed_content_type(file)
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


@router.get('/{media_id}', summary='Получение изображения по ID')
async def get_image(media_id: str) -> FileResponse:
    """Получение изображения по ID."""
    from api.validators.media import check_media_id, media_exist

    media_id = check_media_id(media_id)
    filename = f'{media_id}.jpg'
    file_path = media_exist(MEDIA_PATH / filename)

    return FileResponse(
        path=file_path,
        media_type='image/jpeg',
        filename=filename,
    )
