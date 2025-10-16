from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, require_manager_or_admin
from api.table_service import TableService
from core.db import get_session
from models.user import User
from schemas.table import TableCreate, TableInfo, TableUpdate

router = APIRouter(prefix='/cafe/{cafe_id}/tables', tags=['Столы'])


@router.get(
    '/',
    response_model=List[TableInfo],
    summary='Список столов в кафе',
)
async def get_all_tables_in_cafe(
    cafe_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    show_all: bool = False,
) -> List[TableInfo]:
    """Получает список столов в кафе с фильтрацией по активности и роли."""
    tables = await TableService.get_all_tables(
        session=session,
        cafe_id=cafe_id,
        current_user=current_user,
        show_all=show_all,
    )
    if tables is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Кафе не найдено',
        )
    return tables


@router.get(
    '/{table_id}',
    response_model=TableInfo,
    summary='Информация о столе в кафе по его ID',
)
async def get_table_by_id(
    cafe_id: int,
    table_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TableInfo:
    """Получает один стол по ID."""
    table = await TableService.get_table(
        session=session,
        cafe_id=cafe_id,
        table_id=table_id,
        current_user=current_user,
    )
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Стол не найден в данном кафе',
        )
    return table


@router.post(
    '/',
    response_model=TableInfo,
    status_code=status.HTTP_201_CREATED,
    summary='Создание нового стола в кафе',
)
async def create_table(
    cafe_id: int,
    table_in: TableCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_manager_or_admin),
) -> TableInfo:
    """Создает новый стол в указанном кафе."""
    table_in.cafe_id = cafe_id
    return await TableService.create_table(
        session=session,
        table_in=table_in,
    )


@router.patch(
    '/{table_id}',
    response_model=TableInfo,
    summary='Обновление информации о столе в кафе по его ID',
)
async def update_table(
    cafe_id: int,
    table_id: int,
    table_in: TableUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_manager_or_admin),
) -> TableInfo:
    """Обновляет стол по ID с проверкой принадлежности к кафе."""
    table = await TableService.update_table(
        session=session,
        table_id=table_id,
        table_in=table_in,
    )
    if not table or table.cafe.id != cafe_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Стол не найден в данном кафе',
        )
    return table
