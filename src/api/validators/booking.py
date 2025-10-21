from datetime import date

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.exceptions import err
from models.booking import Booking, BookingStatus
from models.cafe import Cafe
from models.slots import Slot
from models.table import Table


async def booking_exists(booking_id: int, session: AsyncSession) -> Booking:
    """Проверяет, что бронь существует и активна."""
    booking = await session.get(Booking, booking_id)
    if booking is None or booking.status != BookingStatus.ACTIVE.value:
        return err(
            404,
            'Такой брони нет или она не активна.',
            status.HTTP_404_NOT_FOUND,
        )
    return booking


async def check_all_objects_id(
    objects_dict: dict,
    session: AsyncSession,
) -> None:
    """Проверяет существование кафе, слотов и столов по их ID.

    Затем валидирует отсутствие конфликтующих бронирований.
    """
    cafe_id = objects_dict[Cafe]
    slots_id = objects_dict[Slot]
    tables_id = objects_dict[Table]

    cafe = await session.get(Cafe, cafe_id)
    if cafe is None:
        return err(
            404,
            f'Нет кафе с ID: {cafe_id}',
            status.HTTP_404_NOT_FOUND,
        )

    for slot_id in slots_id:
        slot = await session.get(_slots, slot_id)
        if slot is None:
            err(
                404,
                f'Нет временного слота с ID: {slot_id}',
                status.HTTP_404_NOT_FOUND,
            )

    for table_id in tables_id:
        table = await session.get(Table, table_id)
        if table is None:
            err(
                404,
                f'Нет стола с ID: {table_id}',
                status.HTTP_404_NOT_FOUND,
            )

    await check_booking_conflicts(cafe_id, slots_id, tables_id, session)
    return None  # RET503


async def check_booking_conflicts(
    cafe_id: int,
    slots_id: list[int],
    tables_id: list[int],
    session: AsyncSession,
) -> None:
    """Проверяет наличие конфликтующих бронирований."""
    stmt = select(Booking).where(
        Booking.cafe_id == cafe_id,
        Booking.slots_id.in_(slots_id),
        Booking.tables_id.in_(tables_id),
        Booking.status == BookingStatus.ACTIVE.value,
    )
    result = await session.execute(stmt)
    existing_bookings = result.scalars().all()

    if existing_bookings:
        conflicting_slots = list(set(b.slots_id for b in existing_bookings))
        conflicting_tables = list(set(b.tables_id for b in existing_bookings))
        err(
            422,
            'Найдены конфликтующие бронирования. '
            f'Слоты: {conflicting_slots}, '
            f'Столы: {conflicting_tables}',
            status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    return None  # RET503


async def check_booking_date(booking_date: date) -> None:
    """Проверяет, что дата бронирования не в прошлом."""
    if booking_date < date.today():
        err(
            422,
            'Нельзя назначить бронь на прошедшую дату!',
            status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    return None  # RET503
