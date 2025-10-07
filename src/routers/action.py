from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_session
from src.models.action import Action
from src.models.cafe import Cafe
from src.schemas.action import ActionCreate, ActionOut, ActionUpdate

router = APIRouter(prefix='/actions', tags=['actions'])


def to_out(action: Action) -> ActionOut:
    """Преобразует ORM-модель Action в схему для ответа."""
    cafe_ids: list[int] = [c.id for c in getattr(action, 'cafes', [])]
    return ActionOut(
        id=action.id,
        description=action.description,
        photo_id=action.photo_id,
        active=action.active,
        cafe_ids=cafe_ids,
    )


@router.post('/', response_model=ActionOut)
async def create_action(
    data: ActionCreate,
    session: AsyncSession = Depends(get_session),
) -> ActionOut:
    """Создание новой акции."""
    action: Action = Action(
        description=data.description,
        photo_id=data.photo_id,
        active=data.active,
    )
    if data.cafe_ids:
        cafes: list[Cafe] = (
            (
                await session.execute(
                    select(Cafe).where(Cafe.id.in_(data.cafe_ids)),
                )
            )
            .scalars()
            .all()
        )
        action.cafes = cafes

    session.add(action)
    await session.commit()
    await session.refresh(action)
    _ = getattr(action, 'cafes', [])
    return to_out(action)


@router.get('/', response_model=list[ActionOut])
async def list_actions(
    session: AsyncSession = Depends(get_session),
    cafe_id: int | None = Query(None),
    q: str | None = Query(None),
    active: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
) -> list[ActionOut]:
    """Получение списка акций с фильтрами и пагинацией."""
    stmt = select(Action)
    if q:
        stmt = stmt.where(Action.description.ilike(f'%{q}%'))
    if active is not None:
        stmt = stmt.where(Action.active == active)
    if cafe_id is not None:
        stmt = stmt.join(Action.cafes).where(Cafe.id == cafe_id)

    res = await session.execute(stmt.offset(skip).limit(limit))
    actions: list[Action] = res.scalars().unique().all()
    return [to_out(a) for a in actions]


@router.get('/{action_id}', response_model=ActionOut)
async def get_action(
    action_id: int,
    session: AsyncSession = Depends(get_session),
) -> ActionOut:
    """Получить акцию по ID."""
    action: Action | None = await session.get(Action, action_id)
    if not action:
        raise HTTPException(status_code=404, detail='Action not found')
    _ = getattr(action, 'cafes', [])
    return to_out(action)


@router.patch('/{action_id}', response_model=ActionOut)
async def update_action(
    action_id: int,
    data: ActionUpdate,
    session: AsyncSession = Depends(get_session),
) -> ActionOut:
    """Обновить данные акции."""
    action: Action | None = await session.get(Action, action_id)
    if not action:
        raise HTTPException(status_code=404, detail='Action not found')

    for key, value in data.model_dump(
        exclude_unset=True,
        exclude={'cafe_ids'},
    ).items():
        setattr(action, key, value)

    if data.cafe_ids is not None:
        cafes: list[Cafe] = (
            (
                await session.execute(
                    select(Cafe).where(Cafe.id.in_(data.cafe_ids)),
                )
            )
            .scalars()
            .all()
        )
        action.cafes = cafes

    await session.commit()
    await session.refresh(action)
    _ = getattr(action, 'cafes', [])
    return to_out(action)


@router.delete('/{action_id}', status_code=204)
async def delete_action(
    action_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Мягкое удаление акции."""
    action: Action | None = await session.get(Action, action_id)
    if not action:
        raise HTTPException(status_code=404, detail='Action not found')
    action.active = False
    await session.commit()
