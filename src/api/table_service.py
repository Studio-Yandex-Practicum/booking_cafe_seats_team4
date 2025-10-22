from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from api.validators.cafe import check_cafe_permissions
from api.exceptions import err
from api.validators.cafe import get_cafe_or_404
from api.validators.table import get_table_in_cafe_or_404
from crud.table import table_crud
from models.user import User
from schemas.table import TableCreate, TableInfo, TableUpdate
from schemas.user import UserRole


class TableService:
    """Сервисный слой для работы со столами."""

    @staticmethod
    async def get_all_tables(
        session: AsyncSession,
        cafe_id: int,
        current_user: User,
        show_all: bool = False,
    ) -> List[TableInfo]:
        """Получает список столов. Выбрасывает 404, если кафе не найдено."""
        await get_cafe_or_404(cafe_id, session)

        tables_db = await table_crud.get_multi(
            session=session,
            cafe_id=cafe_id,
        )
        is_admin_or_manager = current_user.role in (
            UserRole.ADMIN,
            UserRole.MANAGER,
        )
        if not (is_admin_or_manager and show_all):
            tables_db = [table for table in tables_db if table.is_active]

        return [
            TableInfo.model_validate(
                table,
                from_attributes=True,
            )
            for table in tables_db
        ]

    @staticmethod
    async def get_table(
        session: AsyncSession,
        cafe_id: int,
        table_id: int,
        current_user: User,
    ) -> TableInfo:
        """Получает один стол, проверяя кафе и права доступа."""
        table_db = await get_table_in_cafe_or_404(cafe_id, table_id, session)

        is_admin_or_manager = current_user.role in (
            UserRole.ADMIN,
            UserRole.MANAGER,
        )
        if not table_db.is_active and not is_admin_or_manager:
            raise err('NOT_FOUND', 'Стол не найден в данном кафе', 404)

        return TableInfo.model_validate(table_db, from_attributes=True)

    @staticmethod
    async def create_table(
        session: AsyncSession,
        cafe_id: int,
        table_in: TableCreate,
        current_user: User,
    ) -> TableInfo:
        """Создает новый стол в указанном кафе."""
        cafe_db = await get_cafe_or_404(cafe_id, session)
        check_cafe_permissions(cafe=cafe_db, user=current_user)
        new_table_db = await table_crud.create(
            table_in,
            session,
            cafe_id=cafe_id,
        )

        return TableInfo.model_validate(new_table_db, from_attributes=True)

    @staticmethod
    async def update_table(
        session: AsyncSession,
        cafe_id: int,
        table_id: int,
        table_in: TableUpdate,
        current_user: User,
    ) -> TableInfo:
        """Обновляет стол, проверяя его принадлежность к кафе."""
        db_table = await get_table_in_cafe_or_404(cafe_id, table_id, session)
        check_cafe_permissions(cafe=db_table.cafe, user=current_user)
        updated_table_db = await table_crud.update(
            db_obj=db_table,
            obj_in=table_in,
            session=session,
        )

        return TableInfo.model_validate(updated_table_db, from_attributes=True)
