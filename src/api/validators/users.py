from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.schemas.user import UserCreate


async def get_user_or_404(user_id: int, session: AsyncSession) -> User:
    """Вернуть пользователя по id или 404 Not Found."""
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found',
        )
    return user


def ensure_contact_present_on_create(payload: UserCreate) -> None:
    """На создание пользователя требуется указать email или phone."""
    if not (payload.email or payload.phone):
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
