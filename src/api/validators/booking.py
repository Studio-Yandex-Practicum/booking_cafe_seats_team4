from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud.booking import booking_crud
from models.booking import Booking, BookingStatus


async def booking_exists(booking_id: int, session: AsyncSession) -> Booking:
    """Проверяет, что бронь существует и активна."""
    booking = await session.get(Booking, booking_id)
    if booking is None or booking.status != BookingStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Такой брони нет или она не активна.',
        )
    return booking


async def check_all_objects_id(
        slots_id: list[int],
        tables_id: list[int],
        cafe_id: int,
        session: AsyncSession) -> None:
    pass


async def check_booking_date(
        booking_date: date,
        session: AsyncSession,
) -> None:
    booking = await booking_crud.get_booking_by_date(
        booking_date,
        session,
    )
    if booking is not None:
        raise HTTPException(
            status_code=400,
            detail='Бронирование на эту дату уже сушествует!',
        )
    if booking_date < date.today():
        raise HTTPException(
            status_code=400,
            detail='Нельзя назначить бронь на прошедшую дату!',
        )
