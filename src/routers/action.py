from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from models.action import Action
from models.cafe import Cafe
from schemas.action import ActionCreate, ActionOut, ActionUpdate

router = APIRouter(prefix='/actions', tags=['actions'])


def to_out(a: Action) -> ActionOut:
    """Собрать ActionOut из ORM-модели с перечислением cafe_ids."""
    return ActionOut(
        id=a.id,
        description=a.description,
        photo_id=getattr(a, 'photo_id', None),
        cafe_ids=[c.id for c in getattr(a, 'cafes', [])],
    )


@router.post('/', response_model=ActionOut)
async def create_action(
    data: ActionCreate,
    session: AsyncSession = Depends(get_session),
) -> ActionOut:
    """Создать акцию и (опционально) привязать к списку кафе."""
    payload = data.model_dump()
    action = Action(
        description=payload['description'],
        photo_id=payload.get('photo_id'),
    )

    cafe_ids = payload.get('cafe_ids') or []
    if cafe_ids:
        cafes = (
            (await session.execute(select(Cafe).where(Cafe.id.in_(cafe_ids))))
            .scalars()
            .all()
        )
        if len(cafes) != len(set(cafe_ids)):
            raise HTTPException(
                status_code=400,
                detail='Некоторые cafe_id не найдены',
            )
        action.cafes = cafes

    session.add(action)
    await session.commit()
    await session.refresh(action)
    return to_out(action)


@router.get('/', response_model=list[ActionOut])
async def list_actions(
    session: AsyncSession = Depends(get_session),
    cafe_id: int | None = Query(None),
    q: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
) -> list[ActionOut]:
    """Список акций с фильтрами по cafe_id и подстроке в описании."""
    stmt = select(Action)
    if q:
        stmt = stmt.where(Action.description.ilike(f'%{q}%'))
    if cafe_id is not None:
        stmt = stmt.join(Action.cafes).where(Cafe.id == cafe_id)

    res = await session.execute(stmt.offset(skip).limit(limit))
    actions = res.scalars().unique().all()
    return [to_out(a) for a in actions]


@router.get('/{action_id}', response_model=ActionOut)
async def get_action(
    action_id: int,
    session: AsyncSession = Depends(get_session),
) -> ActionOut:
    """Получить акцию по ID."""
    action = await session.get(Action, action_id)
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
    """Частично обновить акцию."""
    action = await session.get(Action, action_id)
    if not action:
        raise HTTPException(status_code=404, detail='Action not found')

    payload = data.model_dump(exclude_unset=True)

    if 'description' in payload:
        action.description = payload['description']
    if 'photo_id' in payload:
        action.photo_id = payload['photo_id']

    if 'cafe_ids' in payload and payload['cafe_ids'] is not None:
        cafes = (
            (
                await session.execute(
                    select(Cafe).where(Cafe.id.in_(payload['cafe_ids'])),
                )
            )
            .scalars()
            .all()
        )
        if len(cafes) != len(set(payload['cafe_ids'])):
            raise HTTPException(
                status_code=400,
                detail='Некоторые cafe_id не найдены',
            )
        action.cafes = cafes

    await session.commit()
    await session.refresh(action)
    return to_out(action)


@router.delete('/{action_id}', status_code=204)
async def delete_action(
    action_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Удалить акцию (жёстко)."""
    action = await session.get(Action, action_id)
    if not action:
        raise HTTPException(status_code=404, detail='Action not found')

    await session.delete(action)
    await session.commit()
