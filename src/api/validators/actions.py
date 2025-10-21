from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from api.exceptions import err
from crud.actions import actions_crud
from models.action import Action


async def get_action_or_404(action_id: int, session: AsyncSession) -> Action:
    """Получить объект акции по ID или выбросить ошибку 404."""
    action = await actions_crud.get(obj_id=action_id, session=session)
    if action_id <= 0:
        raise err(
            'INVALID_ID_FORMAT',
            'ID должен быть положительным числом',
            400,
        )
    if not action:
        raise err('NOT_FOUND', 'Акция не найдена', 404)
    return action
