from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import require_manager_or_admin
from core.db import get_session
from crud.action import action_crud
from models.user import User
from schemas.action import ActionCreate, ActionOut, ActionUpdate, ActionList
from api.validators.actions import (
    action_exists,
    action_active,
    cafe_exists,
    user_can_manage_cafe,
)

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("/", response_model=ActionList)
async def list_actions(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: str | None = Query(None, description="Поиск по описанию акции"),
    cafe_id: int | None = Query(None, description="Фильтр по кафе"),
    only_active: bool | None = Query(None, description="Только активные"),
):
    """
    Получить список акций с фильтрацией, поиском и пагинацией.
    """
    total, items = await action_crud.get_multi(
        session,
        limit=limit,
        offset=offset,
        q=q,
        cafe_id=cafe_id,
        only_active=only_active,
    )
    out_items = [
        ActionOut(
            id=it.id,
            description=it.description,
            photo_id=it.photo_id,
            active=it.is_active,
            cafe_ids=[c.id for c in it.cafes],
        )
        for it in items
    ]
    return ActionList(total=total, items=out_items)


@router.get("/active", response_model=ActionList)
async def list_active_actions(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: str | None = Query(None),
    cafe_id: int | None = Query(None),
):
    """
    Получить только активные акции (короткая версия эндпоинта /actions).
    """
    total, items = await action_crud.get_multi(
        session,
        limit=limit,
        offset=offset,
        q=q,
        cafe_id=cafe_id,
        only_active=True,
    )
    out_items = [
        ActionOut(
            id=it.id,
            description=it.description,
            photo_id=it.photo_id,
            active=it.is_active,
            cafe_ids=[c.id for c in it.cafes],
        )
        for it in items
    ]
    return ActionList(total=total, items=out_items)


@router.get("/{action_id}", response_model=ActionOut)
async def get_action(
    action_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Получить детальную информацию об акции по ID."""
    action = await action_exists(action_id, session)
    return ActionOut(
        id=action.id,
        description=action.description,
        photo_id=action.photo_id,
        active=action.is_active,
        cafe_ids=[c.id for c in action.cafes],
    )


@router.post("/",
             response_model=ActionOut, status_code=status.HTTP_201_CREATED)
async def create_action(
    data: ActionCreate,
    current_user: Annotated[User, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Создать новую акцию (только менеджер или админ)."""
    # Проверяем права на кафе, если указаны
    if data.cafe_ids:
        for cafe_id in data.cafe_ids:
            cafe = await cafe_exists(cafe_id, session)
            user_can_manage_cafe(current_user, cafe)

    action = await action_crud.create(
        session,
        description=data.description,
        photo_id=data.photo_id,
        cafe_ids=data.cafe_ids,
    )
    await session.commit()
    await session.refresh(action)
    return ActionOut(
        id=action.id,
        description=action.description,
        photo_id=action.photo_id,
        active=action.is_active,
        cafe_ids=[c.id for c in action.cafes],
    )


@router.patch("/{action_id}", response_model=ActionOut)
async def update_action(
    action_id: int,
    data: ActionUpdate,
    current_user: Annotated[User, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Обновить данные существующей акции (только менеджер или админ)."""
    action = await action_exists(action_id, session)

    # Проверяем права на кафе, если указаны новые
    if data.cafe_ids:
        for cafe_id in data.cafe_ids:
            cafe = await cafe_exists(cafe_id, session)
            user_can_manage_cafe(current_user, cafe)

    action = await action_crud.update(
        session,
        action,
        description=data.description,
        photo_id=data.photo_id,
        active=data.active,
        cafe_ids=data.cafe_ids,
    )
    await session.commit()
    await session.refresh(action)
    return ActionOut(
        id=action.id,
        description=action.description,
        photo_id=action.photo_id,
        active=action.is_active,
        cafe_ids=[c.id for c in action.cafes],
    )


@router.delete("/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action(
    action_id: int,
    current_user: Annotated[User, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Мягкое удаление акции (деактивация) - только менеджер или админ."""
    action = await action_exists(action_id, session)

    # Проверяем права на кафе акции
    for cafe in action.cafes:
        user_can_manage_cafe(current_user, cafe)

    await action_crud.soft_delete(session, action)
    await session.commit()
    return None
