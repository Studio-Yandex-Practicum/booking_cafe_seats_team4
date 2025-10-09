from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user, require_manager_or_admin
from api.validators.users import (
    apply_user_update,
    ensure_contact_present_on_create,
    ensure_user_active,
    get_user_or_404,
)
from core.db import get_session
from core.security import hash_password
from models.user import User
from schemas.user import UserCreate, UserInfo, UserUpdate

router = APIRouter(prefix='/users', tags=['Пользователи'])


@router.get('', response_model=list[UserInfo], summary='Список пользователей')
async def list_users(
    _: Annotated[User, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[User]:
    """Возвращает список всех пользователей."""
    rows = await session.scalars(select(User).order_by(User.id))
    return list(rows)


@router.post(
    '',
    response_model=UserInfo,
    summary='Регистрация нового пользователя',
)
async def create_user(
    payload: UserCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Создаёт нового пользователя."""
    ensure_contact_present_on_create(payload)

    new_user = User(
        username=payload.username,
        email=payload.email,
        phone=payload.phone,
        tg_id=payload.tg_id,
        role=0,
        is_active=True,
        password_hash=hash_password(payload.password),
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


@router.get('/me', response_model=UserInfo, summary='Текущий пользователь')
async def get_me(
    current: Annotated[User, Depends(get_current_user)],
) -> User:
    """Возвращает данные текущего пользователя."""
    return current


@router.patch('/me', response_model=UserInfo, summary='Изменить свои данные')
async def patch_me(
    payload: UserUpdate,
    current: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Позволяет изменить данные текущего пользователя."""
    # Себе роль менять нельзя
    if payload.role is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Changing own role is forbidden',
        )

    apply_user_update(current, payload)
    await session.commit()
    await session.refresh(current)
    return current


@router.get(
    '/{user_id}',
    response_model=UserInfo,
    summary='Получить пользователя по id',
)
async def get_user_by_id(
    user_id: int,
    _: Annotated[User, Depends(require_manager_or_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Возвращает пользователя по его ID."""
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
) -> User:
    """Изменяет данные пользователя по ID."""
    user = await get_user_or_404(user_id, session)
    ensure_user_active(user)

    apply_user_update(user, payload)
    await session.commit()
    await session.refresh(user)
    return user
