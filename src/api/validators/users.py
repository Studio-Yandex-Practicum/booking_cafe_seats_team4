from typing import Iterable

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from api.deps import get_current_user
from api.exceptions import bad_request, err, forbidden, not_found
from core.security import hash_password
from models.user import User
from schemas.user import UserCreate, UserRole, UserUpdate

USER_FIELDS_TO_LOAD = [
    User.id, User.username, User.email, User.phone, User.tg_id,
    User.role, User.is_active, User.created_at, User.updated_at,
]


async def get_user_or_404(user_id: int, session: AsyncSession) -> User:
    """Вернуть пользователя по id или 404 Not Found."""
    query = (
        select(User)
        .where(User.id == user_id)
        .options(load_only(*USER_FIELDS_TO_LOAD))
    )
    result = await session.execute(query)
    user = result.scalars().first()

    if user is None:
        raise not_found('Пользователь не найден')
    return user


def ensure_contact_present_on_create(payload: UserCreate) -> None:
    """На создание пользователя требуется указать email или phone."""
    email = (payload.email or '').strip()
    phone = (payload.phone or '').strip()
    if not (email or phone):
        raise bad_request('Необходимо указать email или телефон')


def ensure_user_active(user: User) -> None:
    """Запретить операции над неактивным пользователем (403)."""
    if not user.is_active:
        raise forbidden('Пользователь неактивен')


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

    if 'password' in data:
        entity.password_hash = hash_password(data.pop('password'))

    if 'role' in data and data['role'] is not None:
        try:
            data['role'] = int(UserRole(data['role']))
        except ValueError:
            raise err('ROLE_UNKNOWN', 'Неизвестная роль', 422)

    for field in _MUTABLE_FIELDS:
        if field in data:
            setattr(entity, field, data[field])


def check_user_is_manager_or_admin(
    user: User = Depends(get_current_user),
) -> bool:
    """Проверяет, что user является MANAGER или ADMIN."""
    if user.role not in (int(UserRole.MANAGER), int(UserRole.ADMIN)):
        return False
    return True
