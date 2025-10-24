from datetime import date
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.exceptions import bad_request, forbidden, not_found, unprocessable
from models.booking import Booking, BookingStatus
from models.cafe import Cafe
from models.slots import Slot
from models.table import Table
from models.user import User
from schemas.booking import BookingCreate
from schemas.user import UserRole


async def booking_exists(booking_id: int, session: AsyncSession) -> Booking:
    """Проверяет, что бронь существует и активна."""
    booking = await session.get(Booking, booking_id)
    if booking is None or booking.status != BookingStatus.ACTIVE.value:
        raise not_found('Такой брони нет или она не активна.')
    return booking


async def check_all_objects_id(
    cafe_id: int,
    slots_id: List[int],
    tables_id: List[int],
    session: AsyncSession,
) -> None:
    """Проверяет существование кафе, слотов и столов по их ID.

    Затем валидирует отсутствие конфликтующих бронирований.
    """
    cafe = await session.get(Cafe, cafe_id)
    if cafe is None:
        raise not_found(f'Нет кафе с ID: {cafe_id}')
    for slot_id in slots_id:
        slot = await session.get(Slot, slot_id)
        if slot is None:
            raise not_found(f'Нет временного слота с ID: {slot_id}')

    for table_id in tables_id:
        table = await session.get(Table, table_id)
        if table is None:
            raise not_found(f'Нет стола с ID: {table_id}')

    await check_booking_conflicts(cafe_id, slots_id, tables_id, session)


async def check_booking_conflicts(
    cafe_id: int,
    slots_id: list[int],
    tables_id: list[int],
    booking_date: date,
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
            Booking.booking_date == booking_gate,
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
            err_msg.append(f'Слоты уже заняты: {sorted(conflicting_slots)}')
        if conflicting_tables:
            err_msg.append(f'Столы уже заняты: {sorted(conflicting_tables)}')

        raise bad_request(
            'Найдены конфликтующие бронирования. ' + '; '.join(err_msg),
        )


async def check_booking_date(booking_date: date) -> None:
    """Проверяет, что дата бронирования не в прошлом."""
    if booking_date < date.today():
        raise unprocessable(
            'Нельзя назначить бронь на прошедшую дату!',
        )


async def ban_change_status(
    booking: Booking,
    obj_in: BookingCreate,
) -> None:
    """Изменить прошедшее и активное бронирование по полю status нельзя."""
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, _ in update_data.items():
        if field == 'status' and (
            booking.is_active is True or booking.booking_date < date.today()
        ):
            raise bad_request(
                'Нельзя изменить прошедшее и активное бронирование!',
            )


async def cafe_exists(cafe_id: int, session: AsyncSession) -> Cafe:
    """Проверяет, что кафе существует и активно."""
    cafe = await session.get(Cafe, cafe_id)
    if cafe is None or not cafe.is_active:
        raise not_found('Такого кафе нет или оно не активно.')
    return cafe


async def user_can_manage_cafe(
        user: User, cafe_id: int, session: AsyncSession,
    ) -> None:
    """Проверяет, что текущий пользователь может управлять данным кафе."""
    cafe = await cafe_exists(cafe_id, session)
    if user.role == int(UserRole.ADMIN):
        return
    if user.role == int(UserRole.MANAGER):
        if cafe in user.managed_cafes:
            return
    raise forbidden('У вас нет прав доступа.')
