from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from api.exceptions import err
from crud.cafe import cafe_crud
from models.cafe import Cafe
from schemas.user import UserRole
from models.user import User


async def get_cafe_or_404(cafe_id: int, session: AsyncSession) -> Cafe:
    """Получить объект кафе по ID или выбросить ошибку 404."""
    cafe = await cafe_crud.get(obj_id=cafe_id, session=session)
    if cafe_id <= 0:
        raise err(
            'INVALID_ID_FORMAT',
            'ID должен быть положительным числом',
            400,
        )
    if not cafe:
        raise err('NOT_FOUND', 'Кафе не найдено', 404)
    return cafe


def check_cafe_permissions(
    cafe: Cafe,
    user: User,
) -> None:
    """Проверяет, имеет ли пользователь право управлять кафе.

    - Администратор может всё.
    - Менеджер может управлять только своим кафе.
    """

    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.MANAGER:
        manager_ids = {manager.id for manager in cafe.managers}
        if user.id in manager_ids:
            return
    raise err('FORBIDDEN', 'Недостаточно прав', 403)
