from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import _booking, _cafe, _slots, _table
from models.booking import BookingStatus


async def booking_exists(booking_id: int, session: AsyncSession) -> _booking:
    """Проверяет, что бронь существует и активна."""
    booking = await session.get(_booking, booking_id)
    if booking is None or booking.status != BookingStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Такой брони нет или она не активна.',
        )
    return booking


async def check_all_objects_id(
    objects_dict: dict,
    session: AsyncSession,
) -> None:
    """Проверяет существование кафе, слотов и столов по их ID.

    Затем валидирует отсутствие конфликтующих бронирований.
    """
    cafe_id = objects_dict[_cafe]
    slots_id = objects_dict[_slots]
    tables_id = objects_dict[_table]

    cafe = await session.get(_cafe, cafe_id)
    if cafe is None:
        raise HTTPException(
            status_code=404,
            detail=f'Нет кафе с ID: {cafe_id}',
        )

    for slot_id in slots_id:
        slot = await session.get(_slots, slot_id)
        if slot is None:
            raise HTTPException(
                status_code=404,
                detail=f'Нет временного слота с ID: {slot_id}',
            )

    for table_id in tables_id:
        table = await session.get(_table, table_id)
        if table is None:
            raise HTTPException(
                status_code=404,
                detail=f'Нет стола с ID: {table_id}',
            )

    await check_booking_conflicts(cafe_id, slots_id, tables_id, session)


async def check_booking_conflicts(
    cafe_id: int,
    slots_id: list[int],
    tables_id: list[int],
    session: AsyncSession,
) -> None:
    """Проверяет наличие конфликтующих бронирований."""
    stmt = select(_booking).where(
        _booking.cafe_id == cafe_id,
        _booking.slots_id.in_(slots_id),
        _booking.tables_id.in_(tables_id),
        _booking.status == BookingStatus.ACTIVE.value,
    )
    result = await session.execute(stmt)
    existing_bookings = result.scalars().all()

    if existing_bookings:
        conflicting_slots = list({b.slots_id for b in existing_bookings})
        conflicting_tables = list({b.tables_id for b in existing_bookings})
        raise HTTPException(
            status_code=409,
            detail=(
                'Найдены конфликтующие бронирования. '
                f'Слоты: {conflicting_slots}, '
                f'Столы: {conflicting_tables}'
            ),
        )


async def check_booking_date(booking_date: date) -> None:
    """Проверяет, что дата бронирования не в прошлом."""
    if booking_date < date.today():
        raise HTTPException(
            status_code=400,
            detail='Нельзя назначить бронь на прошедшую дату!',
        )
