from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.exceptions import err
from models.cafe import Cafe
from models.slots import Slot
from models.user import User
from schemas.user import UserRole


async def cafe_exists(cafe_id: int, session: AsyncSession) -> Cafe:
    """Проверяет, что кафе существует и активно."""
    cafe = await session.get(Cafe, cafe_id)
    if cafe is None or not cafe.is_active:
        raise err('NOT_FOUND', 'Такого кафе нет или оно не активно.', 404)
    return cafe


async def slot_exists(slot_id: int, session: AsyncSession) -> Slot:
    """Проверяет, что слот существует."""
    slot = await session.get(Slot, slot_id)
    if slot is None:
        raise err('NOT_FOUND', 'Слот не найден.', 404)
    return slot


def user_can_manage_cafe(user: User, cafe: Cafe) -> None:
    """Проверяет, что текущий пользователь может управлять данным кафе."""
    if user.role == int(UserRole.ADMIN):
        return
    if user.role == int(UserRole.MANAGER):
        if cafe in user.managed_cafes:
            return
    raise err('FORBIDDEN', 'У вас нет прав доступа.', 403)


def slot_active(slot: Slot) -> None:
    """Запрещает операции над неактивным слотом."""
    if not slot.is_active:
        raise err('FORBIDDEN', 'Слот не активен.', 403)


async def validate_no_time_overlap(
    payload: Any,
    session: AsyncSession,
    cafe_id: int,
    exclude_id: int | None = None,
) -> None:
    """Проверяет, что новый слот не пересекается по времени с существующими."""
    new_start = getattr(payload, 'start_time', None)
    new_end = getattr(payload, 'end_time', None)

    if new_start is None or new_end is None:
        return

    stmt = select(Slot).where(Slot.cafe_id == cafe_id)
    if exclude_id:
        stmt = stmt.where(Slot.id != exclude_id)
    res = await session.execute(stmt)
    existing_slots = res.scalars().all()

    for slot in existing_slots:
        if slot.is_active and not (
            new_end <= slot.start_time or new_start >= slot.end_time
        ):
            raise err(
                'BAD_REQUEST',
                'Слот пересекается с другим по времени.',
                400
            )
