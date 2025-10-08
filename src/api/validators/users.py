from typing import Iterable

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password
from models.user import User
from schemas.user import UserCreate, UserUpdate


async def get_user_or_404(user_id: int, session: AsyncSession) -> User:
    """Вернуть пользователя по id или 404 Not Found."""
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found',
        )
    return user


def ensure_contact_present_on_create(payload: UserCreate) -> None:
    """На создание пользователя требуется указать email или phone."""
    email = (payload.email or '').strip()
    phone = (payload.phone or '').strip()
    if not (email or phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='email or phone is required',
        )


def ensure_user_active(user: User) -> None:
    """Запретить операции над неактивным пользователем (403)."""
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Inactive user',
        )


_MUTABLE_FIELDS: Iterable[str] = (
    'username',
    'email',
    'phone',
    'tg_id',
    'role',
)


def apply_user_update(entity: User, update: UserUpdate) -> None:
    """Частичное обновление User, включая смену пароля."""
    data = update.model_dump(exclude_unset=True, exclude_none=True)

    # пароль хэшируем отдельно
    if 'password' in data:
        entity.password_hash = hash_password(data.pop('password'))

    if 'role' in data and data['role'] is not None:
        try:
            data['role'] = int(data['role'])
        except (TypeError, ValueError):
            pass

    # применяем разрешённые поля
    for field in _MUTABLE_FIELDS:
        if field in data:
            setattr(entity, field, data[field])
