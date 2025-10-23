from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.logging import get_user_logger
from core.reqctx import get_request_id, get_user

ModelType = TypeVar('ModelType')
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)


def audit_event(resource: str, action: str, **fields: Any) -> None:
    """Пишет бизнес-аудит: <resource>.<action> + произвольные поля."""
    log = get_user_logger(f'app.audit.{resource}', get_user())
    rid = get_request_id()
    body = ' '.join(f'{k}={v}' for k, v in fields.items())
    if rid:
        body = f'{body} req_id={rid}' if body else 'req_id={rid}'
    log.info('%s.%s %s', resource, action, body)


def _resource_name(model: type[ModelType]) -> str:
    """Имя ресурса для аудита: табличное имя или имя модели в lower."""
    return getattr(model, '__tablename__', model.__name__.lower())


def _collect_fk_fields(obj: Any) -> dict[str, Any]:
    """Собирает id и простые *_id поля для лога."""
    fields: dict[str, Any] = {'id': getattr(obj, 'id', None)}
    for name, val in vars(obj).items():
        if name.startswith('_'):
            continue
        if name.endswith('_id'):
            fields[name] = val
    return fields


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
        user_id: Optional[int] = None,
    ) -> ModelType:
        """Создать объект из схемы `obj_in` и вернуть его."""
        obj_in_data = obj_in.model_dump()
        if user_id is not None:
            obj_in_data['user_id'] = user_id
        db_obj = self.model(**obj_in_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)

        audit_event(
            _resource_name(self.model),
            'created',
            **_collect_fk_fields(db_obj),
        )
        return db_obj

    async def update(
        self,
        db_obj: ModelType,
        obj_in: UpdateSchemaType,
        session: AsyncSession,
    ) -> ModelType:
        """Частично обновить `db_obj` данными из `obj_in` и вернуть его."""
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)

        audit_event(
            _resource_name(self.model),
            'updated',
            id=getattr(db_obj, 'id', None),
        )
        return db_obj

    async def deactivate(
        self,
        db_obj: ModelType,
        session: AsyncSession,
    ) -> ModelType:
        """Деактивация объекта путём изменения поля is_active."""
        if not hasattr(db_obj, 'is_active'):
            raise AttributeError(
                f'Модель {self.model.__name__} не имеет поля is_active',
            )

        db_obj.is_active = False
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)

        audit_event(
            _resource_name(self.model),
            'deactivated',
            id=getattr(db_obj, 'id', None),
        )
        return db_obj
