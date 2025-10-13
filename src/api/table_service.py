from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from crud.cafe import cafe_crud
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
    ) -> List[TableInfo] | None:
        """Получает список столов. Возвращает None, если кафе не найдено."""
        cafe = await cafe_crud.get(obj_id=cafe_id, session=session)
        if not cafe:
            return None

        tables_db = await table_crud.get_multi(
            session=session, cafe_id=cafe_id,
        )

        is_admin_or_manager = current_user.role in (
            UserRole.ADMIN,
            UserRole.MANAGER,
        )
        if not (is_admin_or_manager and show_all):
            tables_db = [table for table in tables_db if table.is_active]

        return [
            TableInfo.model_validate(table, from_attributes=True)
            for table in tables_db
        ]

    @staticmethod
    async def get_table(
        session: AsyncSession, cafe_id: int, table_id: int, current_user: User,
    ) -> TableInfo | None:
        """Получает один стол по ID с проверкой кафе и прав доступа."""
        table_db = await table_crud.get(obj_id=table_id, session=session)
        if not table_db or table_db.cafe_id != cafe_id:
            return None

        is_admin_or_manager = current_user.role in (
            UserRole.ADMIN,
            UserRole.MANAGER,
        )
        if not table_db.is_active and not is_admin_or_manager:
            return None

        return TableInfo.model_validate(table_db, from_attributes=True)

    @staticmethod
    async def create_table(
        session: AsyncSession, table_in: TableCreate,
    ) -> TableInfo:
        """Создает новый стол в базе."""
        new_table_db = await table_crud.create(
            obj_in=table_in, session=session,
        )

        return TableInfo.model_validate(new_table_db, from_attributes=True)

    @staticmethod
    async def update_table(
        session: AsyncSession, table_id: int, table_in: TableUpdate,
    ) -> TableInfo | None:
        """Обновляет стол. Возвращает None, если стол не найден."""
        db_table = await table_crud.get(obj_id=table_id, session=session)
        if not db_table:
            return None

        updated_table_db = await table_crud.update(
            db_obj=db_table, obj_in=table_in, session=session,
        )

        return TableInfo.model_validate(updated_table_db, from_attributes=True)
