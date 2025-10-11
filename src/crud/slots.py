from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.slots import Slot
from schemas.slots import TimeSlotCreate, TimeSlotUpdate


class CRUDSlot(CRUDBase[Slot, TimeSlotCreate, TimeSlotUpdate]):
    """CRUD для временных слотов."""

    async def get_by_cafe(self, cafe_id: int, session: AsyncSession):
        """Возвращает все активные слоты конкретного кафе."""
        stmt = select(Slot).where(
            Slot.cafe_id == cafe_id,
            Slot.is_active.is_(True)
        )
        res = await session.execute(stmt)
        return res.scalars().all()


slot_crud = CRUDSlot(Slot)
