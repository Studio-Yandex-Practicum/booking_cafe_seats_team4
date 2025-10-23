from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.exceptions import err
from api.validators.cafe import check_cafe_permissions, get_cafe_or_404
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
    ) -> CafeInfo:
        """Получает конкретное кафе, проверяет права доступа."""
        cafe_db = await get_cafe_or_404(cafe_id, session)

        is_admin_or_manager = current_user.role in (
            UserRole.ADMIN,
            UserRole.MANAGER,
        )

        if not cafe_db.is_active and not is_admin_or_manager:
            raise err('NOT_FOUND', 'Кафе не найдено', 404)

        return CafeInfo.model_validate(cafe_db, from_attributes=True)

    @staticmethod
    async def create_cafe(
        session: AsyncSession,
        cafe_in: CafeCreate,
        current_user: User,
    ) -> CafeInfo:
        """Создаёт новое кафе.

        Проверяет на дубликат по имени и адресу и обрабатывает ошибки,
        приходящие из CRUD-слоя.
        """
        existing_cafe = await cafe_crud.get_by_name_and_address(
            session=session,
            name=cafe_in.name,
            address=cafe_in.address,
        )
        if existing_cafe:
            raise err(
                'CAFE_DUPLICATE',
                'Кафе с таким названием и адресом уже существует.',
                400,
            )

        if cafe_in.managers_id:
            query = select(User).where(User.id.in_(cafe_in.managers_id))
            result = await session.execute(query)
            potential_managers = result.scalars().all()

            if len(potential_managers) != len(cafe_in.managers_id):
                raise err(
                    'INVALID_MANAGER_ID',
                    'Один или несколько ID менеджеров не найдены',
                    400,
                )

            for user_to_appoint in potential_managers:
                if int(user_to_appoint.role) < UserRole.MANAGER:
                    raise err(
                        'INVALID_ROLE',
                        'Простой пользователь '
                        'не может быть назначен менеджером кафе.',
                        400,
                    )
                if (
                    int(current_user.role) == UserRole.MANAGER
                    and int(user_to_appoint.role) == UserRole.ADMIN
                ):
                    raise err(
                        'FORBIDDEN',
                        'Менеджер не может назначать администратора '
                        'менеджером кафе.',
                        403,
                    )

        try:
            new_cafe_db = await cafe_crud.create(
                obj_in=cafe_in,
                session=session,
            )
            return CafeInfo.model_validate(new_cafe_db, from_attributes=True)
        except ValueError as e:
            await session.rollback()
            raise err('INVALID_MANAGER_ID', str(e), 400)

    @staticmethod
    async def update_cafe(
        session: AsyncSession,
        cafe_id: int,
        cafe_in: CafeUpdate,
        current_user: User,
    ) -> CafeInfo:
        """Обновляет кафе и возвращает его обновлённое представление."""
        db_cafe = await get_cafe_or_404(cafe_id, session)
        check_cafe_permissions(db_cafe, current_user)
        updated_cafe_db = await cafe_crud.update(
            db_obj=db_cafe,
            obj_in=cafe_in,
            session=session,
        )

        return CafeInfo.model_validate(updated_cafe_db, from_attributes=True)
