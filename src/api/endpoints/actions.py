from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.models.action import Action as ActionModel
from src.schemas.action import ActionCreate, ActionUpdate, Action as ActionOut

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("/", response_model=list[ActionOut])
async def list_actions(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: str | None = Query(None, description="Поиск по названию/тексту акции"),
    cafe_id: UUID | None = Query(None,
                                 description="Фильтр по кафе (если у модели"
                                 "есть поле cafe_id)"),
    only_active: bool | None = Query(None, description="Только активные"
                                     "(если у модели есть поле active)"),
):
    """
    Список акций с пагинацией и опциональными фильтрами.
    Фильтры применяются только если соответствующие поля
    есть в модели `Action`.
    """
    filters = []

    # only_active -> Action.active == True (если есть поле)
    if only_active is True and hasattr(ActionModel, "active"):
        filters.append(ActionModel.active.is_(True))

    # cafe_id -> Action.cafe_id == cafe_id (если есть поле)
    if cafe_id is not None and hasattr(ActionModel, "cafe_id"):
        filters.append(ActionModel.cafe_id == cafe_id)

    # q -> поиск по title или name, fallback на description (если поля есть)
    if q:
        ilike = f"%{q.lower()}%"
        or_blocks = []
        if hasattr(ActionModel, "title"):
            or_blocks.append(func.lower(ActionModel.title).like(ilike))
        if hasattr(ActionModel, "name"):
            or_blocks.append(func.lower(ActionModel.name).like(ilike))
        if hasattr(ActionModel, "description"):
            or_blocks.append(func.lower(ActionModel.description).like(ilike))
        if or_blocks:
            # объединяем через OR
            filters.append(
                func.bool_or(*or_blocks) if len(or_blocks) > 1 else or_blocks[
                    0])

    base = select(ActionModel).where(*filters) if filters else select(
        ActionModel)

    # total
    total_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(total_stmt)).scalar_one()

    # items
    # Если есть поле "title" — сортируем по нему, иначе по id
    if hasattr(ActionModel, "title"):
        base = base.order_by(ActionModel.title.asc())
    elif hasattr(ActionModel, "name"):
        base = base.order_by(ActionModel.name.asc())
    else:
        base = base.order_by(ActionModel.id.asc())

    items = (await session.execute(
        base.limit(limit).offset(offset))).scalars().all()
    return items


@router.get("/{action_id}", response_model=ActionOut)
async def get_action(
    action_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Детальная информация об акции по ID."""
    res = await session.execute(select(ActionModel).where(
        ActionModel.id == action_id))
    obj = res.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Action not found")
    return obj


@router.post("/", response_model=ActionOut,
             status_code=status.HTTP_201_CREATED)
async def create_action(
    data: ActionCreate,
    session: AsyncSession = Depends(get_session),
):
    """Создать новую акцию."""
    payload = data.model_dump(exclude_none=True)
    obj = ActionModel(**payload)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


@router.patch("/{action_id}", response_model=ActionOut)
async def update_action(
    action_id: UUID,
    data: ActionUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Частичное обновление акции."""
    res = await session.execute(select(ActionModel).where(
        ActionModel.id == action_id))
    obj = res.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Action not found")

    payload = data.model_dump(exclude_none=True)
    for k, v in payload.items():
        # обновляем только существующие атрибуты модели
        if hasattr(obj, k):
            setattr(obj, k, v)

    await session.commit()
    await session.refresh(obj)
    return obj


@router.delete("/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action(
    action_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Удаление акции.
    Если в модели есть флаг `active`, то превращаем
    в soft-delete (active=False),
    иначе выполняем физическое удаление.
    """
    res = await session.execute(select(ActionModel).where(
        ActionModel.id == action_id))
    obj = res.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Action not found")

    if hasattr(ActionModel, "active"):
        setattr(obj, "active", False)
        await session.commit()
    else:
        await session.delete(obj)
        await session.commit()
    return None
