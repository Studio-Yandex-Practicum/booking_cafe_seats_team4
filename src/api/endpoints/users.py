from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, require_manager_or_admin
from api.exceptions import bad_request, forbidden
from api.validators.users import (
    ensure_contact_present_on_create,
    ensure_user_active,
    get_user_or_404,
)
from core.db import get_session
from crud.users import user_crud
from models.user import User
from schemas.user import UserCreate, UserInfo, UserUpdate

router = APIRouter(prefix='/users', tags=['Пользователи'])


@router.get('', response_model=list[UserInfo], summary='Список пользователей')
async def list_users(
    _: Annotated[User, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[UserInfo]:
    """Возвращает список всех активных пользователей, отсортированный по ID."""
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
    # Запрашиваем хотя бы один контакт (email или phone)
    ensure_contact_present_on_create(payload)

    # При повторе email/phone отдаём 400 CustomError
    try:
        return await user_crud.create_with_hash(payload, session)
    except IntegrityError:
        await session.rollback()
        raise bad_request(
            ('Пользователь с таким email или телефоном уже существует'),
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
) -> UserInfo:
    """Позволяет частично изменить свои данные."""
    if payload.role is not None:
        raise forbidden('Запрещено изменять собственную роль')
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
    _: Annotated[User, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserInfo:
    """Изменяет данные пользователя по ID (через CRUD)."""
    user = await get_user_or_404(user_id, session)
    ensure_user_active(user)
    return await user_crud.update_with_logic(user, payload, session)
