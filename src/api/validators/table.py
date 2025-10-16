from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from api.exceptions import err
from crud.table import table_crud
from models.table import Table


async def get_table_in_cafe_or_404(
    cafe_id: int,
    table_id: int,
    session: AsyncSession,
) -> Table:
    """Получает стол по ID, проверяя его принадлежность к кафе.
    Выбрасывает 404, если стол не найден или не принадлежит кафе.
    Выбрасывает 400, если ID некорректен.
    """
    if table_id <= 0:
        raise err(
            'INVALID_ID_FORMAT',
            'ID стола должен быть положительным числом',
            400,
        )

    table = await table_crud.get(obj_id=table_id, session=session)
    if not table or table.cafe_id != cafe_id:
        raise err('NOT_FOUND', 'Стол не найден в данном кафе', 404)
    return table
