import uuid
import os

from fastapi import HTTPException, status, UploadFile


async def media_allowed_content_type(file: UploadFile) -> UploadFile:
    """Проверяет формат файла"""
    content_types = ['image/jpeg', 'image/png', 'image/jpg']
    if file.content_type not in content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Поддерживаются только JPG и PNG форматы'
        )

    return file


async def check_len_file(file: UploadFile) -> bytes:
    """Проверяет размер файйла"""
    contents = await file.read()
    if len(contents) > 5_242_880:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Размер файла не должен превышать 5Мб.'
        )
    return contents


def check_media_id(media_id: str) -> str:
    try:
        uuid.UUID(media_id, version=4)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail='Неверный формат ID'
        )
    return media_id


def media_exist(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Изображение не найдено'
        )
    return file_path
