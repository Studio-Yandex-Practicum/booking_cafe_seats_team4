from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.slots import Slot
from schemas.slots import TimeSlotCreate, TimeSlotUpdate


class CRUDSlot(CRUDBase[Slot, TimeSlotCreate, TimeSlotUpdate]):
    """CRUD для временных слотов."""

    async def get_by_cafe(
        self,
        cafe_id: int,
        session: AsyncSession,
        only_active: bool = True,
    ) -> list[Slot]:
        """Возвращает все (или только активные) слоты конкретного кафе."""
        stmt = select(Slot).where(Slot.cafe_id == cafe_id)
        if only_active:
            stmt = stmt.where(Slot.is_active.is_(True))
        res = await session.execute(stmt)
        return list(res.scalars().all())

    async def create_with_cafe_id(
        self,
        obj_in: TimeSlotCreate,
        session: AsyncSession,
        cafe_id: int,
    ) -> Slot:
        """Создать слот с cafe_id из пути."""
        obj_in_data = obj_in.model_dump()
        obj_in_data['cafe_id'] = cafe_id
        db_obj = self.model(**obj_in_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj


slot_crud = CRUDSlot(Slot)
