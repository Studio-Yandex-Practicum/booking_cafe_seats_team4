from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from api.exceptions import err
from api.validators.actions import get_action_or_404
from crud.actions import actions_crud
from models.user import User
from schemas.action import ActionCreate, ActionInfo, ActionUpdate
from schemas.user import UserRole


class ActionService:
    """Сервисный слой для работы с акциями."""

    @staticmethod
    async def get_all_actions(
        session: AsyncSession,
        current_user: User,
        show_all: bool = False,
    ) -> List[ActionInfo]:
        """Получает список акций и фильтрует их."""
        actions_db = await actions_crud.get_multi(session=session)
        is_admin_or_manager = current_user.role in (
            UserRole.ADMIN,
            UserRole.MANAGER,
        )
        if not (is_admin_or_manager and show_all):
            actions_db = [action for action in actions_db if action.is_active]

        return [
            ActionInfo.model_validate(action, from_attributes=True)
            for action in actions_db
        ]

    @staticmethod
    async def get_action(
        session: AsyncSession,
        action_id: int,
        current_user: User,
    ) -> ActionInfo:
        """Получает конкретную акцию по id, проверяет права доступа."""
        action_db = await get_action_or_404(action_id, session)
        is_admin_or_manager = current_user.role in (
            UserRole.ADMIN,
            UserRole.MANAGER,
        )
        if not action_db.is_active and not is_admin_or_manager:
            raise err('NOT_FOUND', 'Кафе не найдено', 404)

        return ActionInfo.model_validate(action_db, from_attributes=True)

    @staticmethod
    async def create_action(
        session: AsyncSession,
        action_in: ActionCreate,
    ) -> ActionInfo:
        """Создаёт новую акцию."""
        try:
            action_db = await actions_crud.create(
                obj_in=action_in,
                session=session,
            )
            return ActionInfo.model_validate(action_db, from_attributes=True)
        except ValueError as e:
            await session.rollback()
            raise err('Ошибка создания акции', str(e), 400)

    @staticmethod
    async def update_action(
        session: AsyncSession,
        action_id: int,
        action_in: ActionUpdate,
    ) -> ActionInfo:
        """Обновляет акцию и возвращает ее обновлённое представление."""
        db_action = await get_action_or_404(action_id, session)

        updated_cafe_db = await actions_crud.update(
            db_obj=db_action,
            obj_in=action_in,
            session=session,
        )

        return ActionInfo.model_validate(updated_cafe_db, from_attributes=True)
