from typing import Annotated, List

import redis
from fastapi import APIRouter, Depends, Path, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from api.actions_service import ActionService
from api.deps import get_current_user, require_manager_or_admin
from api.responses import (FORBIDDEN_RESPONSE, INVALID_ID_RESPONSE,
                           NOT_FOUND_RESPONSE, SUCCESSFUL_RESPONSE,
                           UNAUTHORIZED_RESPONSE, VALIDATION_ERROR_RESPONSE)
from celery_tasks.tasks import send_mass_mail
from core.db import get_session
from core.email_templates import ACTION_TEMPLATE
from core.redis import get_redis, redis_cache
from models.user import User
from schemas.action import ActionCreate, ActionInfo, ActionUpdate

router = APIRouter(prefix='/actions', tags=['Акции'])


@router.get(
    '/',
    response_model=List[ActionInfo],
    summary='Список акций',
    responses={
        **UNAUTHORIZED_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
        **SUCCESSFUL_RESPONSE,
    },
)
async def get_all_actions(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
    show_all: Annotated[
        bool,
        Query(
            description=(
                'Показывать все акции или нет. '
                'По умолчанию показывает все акции.'
            ),
        ),
    ] = False,
) -> List[ActionInfo]:
    """Получение списка акций.

    Для администраторов и менеджеров - все акции
    (с возможностью выбора), для пользователей - только активные.
    """

    cache_key = f"actions:{current_user.role}:{show_all}"
    cached_actions = await redis_cache.get_cached_data(cache_key)
    if cached_actions:
        return [ActionInfo(**action) for action in cached_actions]
    actions = await ActionService.get_all_actions(
        session,
        current_user,
        show_all,
    )
    actions_data = jsonable_encoder(actions)
    await redis_cache.set_cached_data(cache_key, actions_data, expire=600)
    return actions


@router.post(
    '/',
    response_model=ActionInfo,
    status_code=status.HTTP_200_OK,
    summary='Новая акция',
    responses={
        **SUCCESSFUL_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def create_action(
    action_in: ActionCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[User, Depends(require_manager_or_admin)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)],

) -> ActionInfo:
    """Создает новую акцию. Только для администраторов и менеджеров."""

    action = await ActionService.create_action(session, action_in)
    email_body = ACTION_TEMPLATE.format(
        action_description=action_in.description,
    )
    send_mass_mail.delay(email_body)
    await redis_cache.delete_pattern("actions:*")
    return action


@router.get(
    '/{action_id}',
    response_model=ActionInfo,
    summary='Информация об акции по ID',
    responses={
        **SUCCESSFUL_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
        **INVALID_ID_RESPONSE,
    },
)
async def get_action_by_id(
    action_id: Annotated[
        int,
        Path(
            description='ID акции',
        ),
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ActionInfo:
    """Получение информации об акции по ID.

    Для администраторов и менеджеров - все акции,
    для пользователей - только активные.
    """
    
    cache_key = f"actions:{current_user.role}"
    cached_actions = await redis_cache.get_cached_data(cache_key)
    
    return await ActionService.get_action(session, action_id, current_user)


@router.patch(
    '/{action_id}',
    response_model=ActionInfo,
    summary='Обновление информации об акции по ID',
    responses={
        **SUCCESSFUL_RESPONSE,
        **NOT_FOUND_RESPONSE,
        **FORBIDDEN_RESPONSE,
        **UNAUTHORIZED_RESPONSE,
        **VALIDATION_ERROR_RESPONSE,
    },
)
async def update_action(
    action_id: Annotated[
        int,
        Path(
            description='ID акции',
        ),
    ],
    action_in: ActionUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[User, Depends(require_manager_or_admin)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)],
) -> ActionInfo:
    """Обновление информации об акции по ID.

    Только для администраторов и менеджеров.
    """

    update_action = await ActionService.update_action(
        session, action_id, action_in)
    await redis_cache.delete_pattern("actions:*")
    return update_action
