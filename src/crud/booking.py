from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.booking import Booking
from models.slots import Slot
from models.table import Table
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

    async def create_booking(
        self,
        obj_in: BookingCreate,
        user_id: Optional[int] = None,
        session: AsyncSession = None,
    ) -> Booking:
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
        return db_obj


booking_crud = CRUDBooking(Booking)
