from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.booking import Booking
from models.user import User
from schemas.booking import BookingCreate, BookingUpdate


class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    """CRUD для бронирования."""

    async def get_multi_booking(
        self,
        session: AsyncSession,
        **kwargs: dict,
    ) -> list[Booking]:
        """Получение всех бронированний с дополнительными параметрами."""
        query = select(Booking)
        show_all = kwargs.pop('show_all', False)
        if not show_all:
            query = query.where(Booking.is_active)
        for field, value in kwargs.items():
            if hasattr(self.model, field) and value is not None:
                query = query.where(getattr(self.model, field) == value)
        result = await session.execute(query)
        return result.scalars().all()

    async def get_booking_current_user(
        self,
        booking_id: int,
        user: User,
        session: AsyncSession,
    ) -> Booking:
        """Получение бронирования для конкретного юзера."""
        query = await session.execute(
            select(Booking).where(
                Booking.booking_id == booking_id,
                Booking.user_id == user.id,
            ),
        )
        return query.scalars().first()


booking_crud = CRUDBooking(Booking)
