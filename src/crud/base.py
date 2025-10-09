from typing import Generic, List, Optional, TypeVar

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar('ModelType')
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Базовый CRUD класс."""

    def __init__(self, model: type[ModelType]) -> None:
        """Сохранить класс ORM-модели, с которой работает CRUD."""
        self.model = model

    async def get(
        self,
        obj_id: int,
        session: AsyncSession,
    ) -> Optional[ModelType]:
        """Вернуть объект по ID или None."""
        return await session.get(self.model, obj_id)

    async def get_multi(
        self,
        session: AsyncSession,
        only_active: bool = True,
    ) -> List[ModelType]:
        """Вернуть список всех объектов модели."""
        stmt = select(self.model)
        if only_active and hasattr(self.model, 'is_active'):
            stmt = stmt.where(self.model.is_active.is_(True))
        result = await session.execute(stmt)
        return result.scalars().all()

    async def create(
        self,
        obj_in: CreateSchemaType,
        session: AsyncSession,
    ) -> ModelType:
        """Создать объект из схемы `obj_in` и вернуть его."""
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj: ModelType,
        obj_in: UpdateSchemaType,
        session: AsyncSession,
    ) -> ModelType:
        """Частично обновить `db_obj` данными из `obj_in` и вернуть его."""
        obj_data = jsonable_encoder(db_obj)
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field in obj_data and hasattr(db_obj, field):
                setattr(db_obj, field, value)

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def deactivate(self, db_obj: ModelType, session: AsyncSession) -> ModelType:
        """Деактивация обьекта путем изменения поля is_active."""
        if not hasattr(db_obj, 'is_active'):
            raise AttributeError(
                f'Модель {self.model.__name__} не имеет поля is_active'
            )

        db_obj.is_active = False
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj
