from typing import Any

from exceptions import bad_request, forbidden, not_found
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.cafe import Cafe
from models.slots import Slot
from models.user import User
from schemas.user import UserRole


async def cafe_exists(cafe_id: int, session: AsyncSession) -> Cafe:
    """Проверяет, что кафе существует и активно."""
    cafe = await session.get(Cafe, cafe_id)
    if cafe is None or not cafe.is_active:
        raise not_found('Такого кафе нет или оно не активно.')
    return cafe


async def slot_exists(slot_id: int, session: AsyncSession) -> Slot:
    """Проверяет, что слот существует."""
    slot = await session.get(Slot, slot_id)
    if slot is None:
        raise not_found('Слот не найден.')
    return slot


def user_can_manage_cafe(user: User, cafe: Cafe) -> None:
    """Проверяет, что текущий пользователь может управлять данным кафе."""
    if user.role == int(UserRole.ADMIN):
        return
    if user.role == int(UserRole.MANAGER):
        if cafe in user.managed_cafes:
            return
    raise forbidden('У вас нет прав доступа.')


def slot_active(slot: Slot) -> None:
    """Запрещает операции над неактивным слотом."""
    if not slot.is_active:
        raise forbidden('Слот не активен.')


async def validate_no_time_overlap(
    payload: Any,
    session: AsyncSession,
    exclude_id: int | None = None,
) -> None:
    """Проверяет, что новый слот не пересекается по времени с существующими."""
    stmt = select(Slot).where(Slot.cafe_id == payload.cafe_id)
    if exclude_id:
        stmt = stmt.where(Slot.id != exclude_id)
    res = await session.execute(stmt)
    existing_slots = res.scalars().all()

    new_start = payload.start_time
    new_end = payload.end_time

    for slot in existing_slots:
        if slot.is_active and not (
            new_end <= slot.start_time or new_start >= slot.end_time
        ):
            raise bad_request('Слот пересекается с другим по времени.')
