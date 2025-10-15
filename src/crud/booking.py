from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.booking import Booking
from models.user import User
from schemas.booking import BookingCreate, BookingUpdate


class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    """CRUD для бронирования."""

    async def get_multi_booking(
            self, session: AsyncSession, **kwargs,
            ) -> list[Booking]:
        query = select(Booking)
        show_all = kwargs.pop('show_all', False)
        if not show_all:
            query = query.where(Booking.is_active == True)
        for field, value in kwargs.items():
            if hasattr(self.model, field) and value is not None:
                query = query.where(getattr(self.model, field) == value)
        result = await session.execute(query)
        return result.scalars().all()

    async def get_booking_by_date(
            self, session: AsyncSession, bookibg_date: date,
            ) -> Booking:
        query = await session.execute(
            select(Booking).where(
                Booking.booking_date == bookibg_date,
            ),
        )
        booking = query.scalars().first()
        return booking

    async def get_booking_current_user(
            self, booking_id: int,  user: User, session: AsyncSession,
            ) -> Booking:
        query = await session.execute(
            select(Booking).where(
                Booking.booking_id == booking_id,
                Booking.user_id == user.id,
            ),
        )
        booking = query.scalars().first()
        return booking


booking_crud = CRUDBooking(Booking)
