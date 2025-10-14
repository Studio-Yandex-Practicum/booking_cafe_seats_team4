from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from crud.cafe import cafe_crud
from models.user import User
from schemas.cafe import CafeCreate, CafeInfo, CafeUpdate
from schemas.user import UserRole


class CafeService:
    """Сервисный слой для работы с кафе."""

    @staticmethod
    async def get_all_cafes(
        session: AsyncSession,
        current_user: User,
        show_all: bool = False,
    ) -> List[CafeInfo]:
        """Получает список кафе и фильтрует их."""
        cafes_db = await cafe_crud.get_multi(session=session)
        is_admin_or_manager = current_user.role in (
            UserRole.ADMIN,
            UserRole.MANAGER,
        )
        if not (is_admin_or_manager and show_all):
            cafes_db = [cafe for cafe in cafes_db if cafe.is_active]

        return [
            CafeInfo.model_validate(cafe, from_attributes=True)
            for cafe in cafes_db
        ]

    @staticmethod
    async def get_cafe(
        session: AsyncSession,
        cafe_id: int,
        current_user: User,
    ) -> CafeInfo | None:
        """Получает конкретное кафе, проверяет права доступа."""
        cafe_db = await cafe_crud.get(obj_id=cafe_id, session=session)

        if not cafe_db:
            return None

        is_admin_or_manager = current_user.role in (
            UserRole.ADMIN,
            UserRole.MANAGER,
        )
        if not cafe_db.is_active and not is_admin_or_manager:
            return None

        return CafeInfo.model_validate(cafe_db, from_attributes=True)

    @staticmethod
    async def create_cafe(
        session: AsyncSession,
        cafe_in: CafeCreate,
    ) -> CafeInfo:
        """Создает новое кафе в базе и возвращает представление."""
        new_cafe_db = await cafe_crud.create(obj_in=cafe_in, session=session)

        return CafeInfo.model_validate(new_cafe_db, from_attributes=True)

    @staticmethod
    async def update_cafe(
        session: AsyncSession,
        cafe_id: int,
        cafe_in: CafeUpdate,
    ) -> CafeInfo | None:
        """Обновляет кафе в базе и возвращает его обновленное представление."""
        db_cafe = await cafe_crud.get(obj_id=cafe_id, session=session)

        if not db_cafe:
            return None

        updated_cafe_db = await cafe_crud.update(
            db_obj=db_cafe,
            obj_in=cafe_in,
            session=session,
        )

        return CafeInfo.model_validate(updated_cafe_db, from_attributes=True)
