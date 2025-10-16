
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models import _booking, _user
from models.booking import Booking
from schemas.booking import BookingCreate, BookingUpdate


class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    """CRUD для бронирования."""

    async def get_multi_booking(
            self, session: AsyncSession, **kwargs: dict,
            ) -> list[Booking]:
        """Получение всех бронированний с дополнительными параметрами."""
        query = select(_booking)
        show_all = kwargs.pop('show_all', False)
        if not show_all:
            query = query.where(_booking.is_active)
        for field, value in kwargs.items():
            if hasattr(self.model, field) and value is not None:
                query = query.where(getattr(self.model, field) == value)
        result = await session.execute(query)
        return result.scalars().all()

    async def get_booking_current_user(
            self, booking_id: int,  user: _user, session: AsyncSession,
            ) -> _booking:
        """Получение бронирования для конкретного юзера."""
        query = await session.execute(
            select(_booking).where(
                _booking.booking_id == booking_id,
                _booking.user_id == user.id,
            ),
        )
        return query.scalars().first()


booking_crud = CRUDBooking(_booking)
