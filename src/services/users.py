from typing import Iterable

from src.core.security import hash_password
from src.models.user import User
from src.schemas.user import UserUpdate

# Поля, которые можно обновлять через UserUpdate.
# (is_active НЕ входит в UserUpdate по спеке!)
_MUTABLE_FIELDS: Iterable[str] = (
    'username',
    'email',
    'phone',
    'tg_id',
    'role',
)


def apply_user_update(entity: User, update: UserUpdate) -> None:
    """Частичное обновление к User, включая смену пароля."""
    data = update.model_dump(exclude_unset=True, exclude_none=True)
    if 'password' in data:
        entity.password_hash = hash_password(data.pop('password'))
    for field in _MUTABLE_FIELDS:
        if field in data:
            setattr(entity, field, data[field])
