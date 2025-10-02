from typing import Iterable

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserUpdate

_MUTABLE_FIELDS: Iterable[str] = (
    'username',
    'email',
    'phone',
    'tg_id',
    'role',
    'is_active',
)


def apply_user_update(entity: User, update: UserUpdate) -> None:
    """Применить partial-обновление к User, включая смену пароля."""
    data = update.model_dump(exclude_unset=True, exclude_none=True)
    if 'password' in data:
        entity.password_hash = hash_password(data.pop('password'))
    for field in _MUTABLE_FIELDS:
        if field in data:
            setattr(entity, field, data[field])
