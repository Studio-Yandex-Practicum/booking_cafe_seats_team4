from __future__ import annotations

from decimal import Decimal
from typing import Annotated, List, Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.schemas.dish import DishCreate, DishOut, DishUpdate
from src.services.dish import DishService

# Роутер блюд: тонкий слой. Никаких прямых SQL — только вызовы сервиса.
router: APIRouter = APIRouter(prefix='/dishes', tags=['dishes'])


def get_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DishService:
    """DI-фабрика: отдаём готовый DishService
    (роутер не знает про сессию/SQL).
    """
    return DishService(session)


ServiceDep = Annotated[DishService, Depends(get_service)]


def _to_out(d) -> DishOut:
    """ORM → DTO: собираем cafe_ids из M2M-связи."""
    return DishOut(
        id=d.id,
        name=d.name,
        price=d.price,
        description=d.description,
        is_available=d.is_available,
        media_id=d.media_id,
        active=d.active,
        cafe_ids=[c.id for c in (d.cafes or [])],
    )


@router.post(
    '/',
    response_model=DishOut,
    status_code=status.HTTP_201_CREATED,
    summary='Создать блюдо',
)
async def create_dish(
    data: Annotated[DishCreate, Body(description='Данные для создания блюда')],
    service: ServiceDep = None,
) -> DishOut:
    """Создать новое блюдо. `cafe_ids` (если переданы)
    — сразу синхронизируются (M2M).
    """
    d = await service.create(
        name=data.name,
        price=data.price,
        description=data.description,
        is_available=data.is_available,
        media_id=data.media_id,
        active=data.active,
        cafe_ids=data.cafe_ids,
    )
    return _to_out(d)


@router.get(
    '/',
    response_model=List[DishOut],
    summary='Список блюд с фильтрами',
    description=(
        'Фильтры: cafe_id (M2M), q (по имени), min/max_price,'
        'available, active. '
        'Пагинация: skip/limit.'
    ),
)
async def list_dishes(
    service: ServiceDep = None,
    cafe_id: Annotated[
        Optional[int], Query(None, ge=1, description='ID кафе(M2M-фильтр)'),
    ] = None,
    q: Annotated[
        Optional[str],
        Query(None, description='Поиск по подстрокев имени блюда'),
    ] = None,
    min_price: Annotated[
        Optional[Decimal], Query(None, ge=0, description='Минимальнаяцена'),
    ] = None,
    max_price: Annotated[
        Optional[Decimal], Query(None, ge=0, description='Максимальнаяцена'),
    ] = None,
    available: Annotated[
        Optional[bool], Query(None, description='Фильтр поis_available'),
    ] = None,
    active: Annotated[
        Optional[bool],
        Query(None, description='Фильтр по soft-deleteполю active'),
    ] = None,
    skip: Annotated[
        int, Query(0, ge=0, description='Смещение для пагинации'),
    ] = 0,
    limit: Annotated[
        int, Query(20, ge=1, le=200, description='Размер страницы (<=200)'),
    ] = 20,
) -> list[DishOut]:
    """Вернуть страницу блюд по заданным фильтрам."""
    dishes = await service.list(
        active=active,
        limit=limit,
        offset=skip,
        cafe_id=cafe_id,
        q=q,
        min_price=min_price,
        max_price=max_price,
        available=available,
    )
    return [_to_out(d) for d in dishes]


@router.get(
    '/{dish_id}',
    response_model=DishOut,
    summary='Получить блюдо по ID',
)
async def get_dish(
    dish_id: Annotated[int, Path(ge=1, description='ID блюда')],
    service: ServiceDep = None,
) -> DishOut:
    """Вернёт блюдо по PK или 404, если не найдено."""
    d = await service.get(dish_id)
    if not d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Dish not found',
        )
    return _to_out(d)


@router.patch(
    '/{dish_id}',
    response_model=DishOut,
    summary='Частично обновить блюдо',
)
async def update_dish(
    dish_id: Annotated[int, Path(ge=1, description='ID блюда')],
    data: Annotated[
        DishUpdate, Body(description='Поля для частичного обновления блюда'),
    ],
    service: ServiceDep = None,
) -> DishOut:
    """Обновляет только переданные поля. Если переданы `cafe_ids`,
    связь с кафе заменяется.
    """
    d = await service.get(dish_id)
    if not d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Dish not found',
        )

    d = await service.update(
        d,
        name=data.name,
        price=data.price,
        description=data.description,
        is_available=data.is_available,
        media_id=data.media_id,
        active=data.active,
        cafe_ids=data.cafe_ids,
    )
    return _to_out(d)


@router.delete(
    '/{dish_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Мягкое удаление блюда',
)
async def delete_dish(
    dish_id: Annotated[int, Path(ge=1, description='ID блюда')],
    service: ServiceDep = None,
) -> None:
    """Помечает блюдо как неактивное (`active=False`)."""
    d = await service.get(dish_id)
    if not d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Dish not found',
        )
    await service.soft_delete(d)
    return
