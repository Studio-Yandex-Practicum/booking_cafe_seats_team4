from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, require_manager_or_admin
from api.exceptions import err
from api.validators.users import (
    ensure_contact_present_on_create,
    ensure_user_active,
    get_user_or_404,
)
from core.db import get_session
from crud.users import user_crud
from models.user import User
from schemas.user import UserCreate, UserInfo, UserRole, UserUpdate

router = APIRouter(prefix='/users', tags=['Пользователи'])


@router.get(
    '',
    response_model=list[UserInfo],
    summary='Список пользователей',
)
async def list_users(
    _: Annotated[User, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[UserInfo]:
    """Возвращает список всех активных пользователей."""
    return await user_crud.list_all(session=session, only_active=True)


@router.post(
    '',
    response_model=UserInfo,
    summary='Регистрация нового пользователя',
    status_code=status.HTTP_200_OK,
)
async def create_user(
    payload: UserCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserInfo:
    """Создаёт нового пользователя (через CRUD)."""
    ensure_contact_present_on_create(payload)

    try:
        return await user_crud.create_with_hash(payload, session)
    except IntegrityError:
        await session.rollback()
        raise err(
            400,
            'Пользователь с таким email или телефоном уже существует',
            400,
        )


@router.get('/me', response_model=UserInfo, summary='Текущий пользователь')
async def get_me(
    current: Annotated[User, Depends(get_current_user)],
) -> UserInfo:
    """Возвращает данные текущего пользователя."""
    return current


@router.patch('/me', response_model=UserInfo, summary='Изменить свои данные')
async def patch_me(
    payload: UserUpdate,
    current: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserInfo | JSONResponse:
    """Позволяет частично изменить свои данные."""
    if payload.role is not None:
        return JSONResponse(
            status_code=403,
            content={
                'code': 403,
                'message': 'Запрещено изменять собственную роль',
            },
        )
    return await user_crud.update_with_logic(current, payload, session)


@router.get(
    '/{user_id}',
    response_model=UserInfo,
    summary='Получить пользователя по id',
)
async def get_user_by_id(
    user_id: int,
    _: Annotated[User, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserInfo:
    """Возвращает пользователя по его ID (только активного)."""
    user = await get_user_or_404(user_id, session)
    ensure_user_active(user)
    return user


@router.patch(
    '/{user_id}',
    response_model=UserInfo,
    summary='Частично изменить пользователя по id',
)
async def patch_user_by_id(
    user_id: int,
    payload: UserUpdate,
    current: Annotated[User, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserInfo:
    """Изменяет данные пользователя по ID."""
    target = await get_user_or_404(user_id, session)
    ensure_user_active(target)

    effective = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not effective:
        raise err(
            422,
            'Нет данных для изменения',
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    new_role = None
    if 'role' in effective and effective['role'] is not None:
        try:
            new_role = UserRole(effective['role'])
        except ValueError:
            raise err(
                422,
                'Неизвестная роль',
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

    if int(current.role) == int(UserRole.MANAGER):
        if current.id == target.id and new_role is not None:
            raise err(
                403,
                'Менеджеру нельзя менять свою роль',
                status.HTTP_403_FORBIDDEN,
            )

        if int(target.role) == int(UserRole.ADMIN) and new_role is not None:
            raise err(
                403,
                'Менеджеру нельзя изменять роль администратора',
                status.HTTP_403_FORBIDDEN,
            )

        if new_role is not None and int(new_role) == int(UserRole.ADMIN):
            raise err(
                403,
                'Менеджеру нельзя назначать роль ADMIN',
                status.HTTP_403_FORBIDDEN,
            )

    return await user_crud.update_with_logic(target, payload, session)
