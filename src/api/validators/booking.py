from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.exceptions import bad_request, not_found
from models.booking import Booking, BookingStatus
from models.cafe import Cafe
from models.slots import Slot
from models.table import Table
from schemas.booking import BookingCreate


async def booking_exists(booking_id: int, session: AsyncSession) -> Booking:
    """Проверяет, что бронь существует и активна."""
    booking = await session.get(Booking, booking_id)
    if booking is None or booking.status != BookingStatus.ACTIVE.value:
        raise not_found('Такой брони нет или она не активна.')
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
        raise not_found(f'Нет кафе с ID: {cafe_id}')
    for id in slots_id:
        slot = await session.get(Slot, id)
        if slot is None:
            raise not_found(f'Нет временного слота с ID: {id}')

    for table_id in tables_id:
        table = await session.get(Table, table_id)
        if table is None:
            raise not_found(f'Нет стола с ID: {table_id}')

    await check_booking_conflicts(cafe_id, slots_id, tables_id, session)
    return None  # RET503


async def check_booking_conflicts(
    cafe_id: int,
    slots_id: list[int],
    tables_id: list[int],
    session: AsyncSession,
) -> None:
    """Проверяет наличие конфликтующих бронирований."""
    stmt = (
        select(Booking)
        .join(Booking.slots_id)
        .join(Booking.tables_id)
        .where(
            Booking.cafe_id == cafe_id,
            Booking.status == BookingStatus.ACTIVE.value,
            Slot.id.in_(slots_id),
            Table.id.in_(tables_id),
        )
    )

    result = await session.execute(stmt)
    conflicting_bookings = result.scalars().all()
    if conflicting_bookings:
        conflicting_slots = set()
        conflicting_tables = set()
        for booking in conflicting_bookings:
            for slot in booking.slots_id:
                if slot.id in slots_id:
                    conflicting_slots.add(slot.id)
            for table in booking.tables_id:
                if table.id in tables_id:
                    conflicting_tables.add(table.id)
        err_msg = []
        if conflicting_slots:
            err_msg.append(f"Слоты уже заняты: {sorted(conflicting_slots)}")
        if conflicting_tables:
            err_msg.append(f"Столы уже заняты: {sorted(conflicting_tables)}")

        raise bad_request(
            "Найдены конфликтующие бронирования. " + "; ".join(err_msg),
        )


async def check_booking_date(booking_date: date) -> None:
    """Проверяет, что дата бронирования не в прошлом."""
    if booking_date < date.today():
        raise bad_request(
            'Нельзя назначить бронь на прошедшую дату!',
        )


async def ban_change_status(
        booking: Booking,
        obj_in: BookingCreate,
) -> None:
    """Проверяет, что изменить прошедшее и активное бронирование по полю status
    нельзя.
    """
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, _ in update_data.items():
        if field == 'status' and (
            booking.is_active == True or booking.booking_date < date.today()
        ):
            raise bad_request(
                'Нельзя изменить прошедшее и активное бронирование!',
            )
