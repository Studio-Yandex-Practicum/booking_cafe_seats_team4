from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.cafe_service import CafeService
from api.deps import get_current_user, require_manager_or_admin
from core.db import get_session
from models.user import User
from schemas.cafe import CafeCreate, CafeInfo, CafeUpdate

router = APIRouter(prefix='/cafes', tags=['Кафе'])


@router.get('/', response_model=List[CafeInfo])
async def get_all_cafes(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    show_all: bool = False,
) -> List[CafeInfo]:
    """Получить список всех кафе."""
    return await CafeService.get_all_cafes(
        session,
        current_user,
        show_all,
    )


@router.post('/', response_model=CafeInfo, status_code=status.HTTP_201_CREATED)
async def create_cafe(
    cafe_in: CafeCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(require_manager_or_admin)],
) -> CafeInfo:
    """Создать новое кафе."""
    return await CafeService.create_cafe(session, cafe_in)


@router.get('/{cafe_id}', response_model=CafeInfo)
async def get_cafe_by_id(
    cafe_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CafeInfo:
    """Получить кафе по ID."""
    cafe = await CafeService.get_cafe(session, cafe_id, current_user)
    if not cafe:
        raise HTTPException(
            status_code=404,
            detail='Кафе не найдено.',
        )
    return cafe


@router.patch('/{cafe_id}', response_model=CafeInfo)
async def update_cafe(
    cafe_id: int,
    cafe_in: CafeUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(require_manager_or_admin)],
) -> CafeInfo:
    """Обновить кафе по ID."""
    updated = await CafeService.update_cafe(session, cafe_id, cafe_in)
    if not updated:
        raise HTTPException(status_code=404, detail='Кафе не найдено')
    return updated
