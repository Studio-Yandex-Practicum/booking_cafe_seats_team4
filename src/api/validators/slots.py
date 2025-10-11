from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.cafe import Cafe
from models.slots import Slot
from models.user import User
from schemas.user import UserRole


async def cafe_exists(cafe_id: int, session: AsyncSession) -> Cafe:
    """Проверяет, что кафе существует и активно."""
    cafe = await session.get(Cafe, cafe_id)
    if cafe is None or not cafe.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Такого кафе нет или оно не активно.',
        )
    return cafe


async def slot_exists(slot_id: int, session: AsyncSession) -> Slot:
    """Проверяет, что слот существует."""
    slot = await session.get(Slot, slot_id)
    if slot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Слот не найден.',
        )
    return slot


def user_can_manage_cafe(user: User, cafe: Cafe) -> None:
    """Проверяет, что текущий пользователь может управлять данным кафе."""
    if user.role == int(UserRole.ADMIN):
        return

    if user.role == int(UserRole.MANAGER):
        if cafe in user.managed_cafes:
            return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail='У вас нет прав доступа.',
    )


def slot_active(slot: Slot) -> None:
    """Запрещает операции над неактивным слотом."""
    if not slot.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Слот не активен.',
        )
