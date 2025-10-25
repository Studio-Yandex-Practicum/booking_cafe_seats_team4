from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.booking import Booking
from models.slots import Slot
from models.table import Table
from models.user import User
from schemas.booking import BookingCreate, BookingUpdate, BookingInfo

from .base import CRUDBase, audit_event


class CRUDBooking(CRUDBase[Booking, BookingCreate, BookingUpdate]):
    """CRUD для бронирования."""

    async def get_multi_booking(
        self,
        session: AsyncSession,
        **kwargs: dict,
    ) -> list[BookingInfo]:
        """Получение всех бронированний с дополнительными параметрами."""
        query = select(Booking)
        show_all = kwargs.pop('show_all', False)
        if not show_all:
            query = query.where(Booking.is_active)
        for field, value in kwargs.items():
            if hasattr(self.model, field) and value is not None:
                query = query.where(getattr(self.model, field) == value)
        result = await session.execute(query)
        bookings_db = result.scalars().all()
        return [
            BookingInfo.model_validate(
                booking, from_attributes=True
            ) for booking in bookings_db]

    async def get_booking_current_user(
        self,
        booking_id: int,
        user: User,
        session: AsyncSession,
    ) -> BookingInfo:
        """Получение бронирования для конкретного юзера."""
        query = await session.execute(
            select(Booking).where(
                Booking.booking_id == booking_id,
                Booking.user_id == user.id,
            ),
        )
        booking_db = query.scalars().first()
        if booking_db:
            return BookingInfo.model_validate(booking_db, from_attributes=True)
        return None

    async def create_booking(
        self,
        obj_in: BookingCreate,
        user_id: Optional[int] = None,
        session: AsyncSession = None,
    ) -> BookingInfo:
        """Создать бронирование с обработкой отношений."""
        slots = await session.execute(
            select(Slot).where(Slot.id.in_(obj_in.slots_id)),
        )
        slots_objs = slots.scalars().all()
        tables = await session.execute(
            select(Table).where(Table.id.in_(obj_in.tables_id)),
        )
        tables_objs = tables.scalars().all()
        obj_in_data = obj_in.model_dump(exclude={'slots_id', 'tables_id'})
        if user_id is not None:
            obj_in_data['user_id'] = user_id
        db_obj = self.model(**obj_in_data)
        db_obj.slots_id = slots_objs
        db_obj.tables_id = tables_objs
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)

        audit_event(
            'booking',
            'created',
            id=(
                getattr(db_obj, 'id', None)
                or getattr(db_obj, 'booking_id', None)
            ),
            user_id=getattr(db_obj, 'user_id', None),
        )

        return BookingInfo.model_validate(db_obj, from_attributes=True)


booking_crud = CRUDBooking(Booking)
