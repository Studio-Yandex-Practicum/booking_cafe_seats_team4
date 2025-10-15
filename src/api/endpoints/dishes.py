from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session
from schemas.dish import DishCreate, DishOut, DishUpdate, DishList
from crud.dish import dish_crud

router = APIRouter(prefix="/dishes", tags=["dishes"])


@router.get("/", response_model=DishList)
async def list_dishes(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: str | None = Query(None, description="Поиск по имени блюда"),
    cafe_id: int | None = Query(None, description="Фильтр по кафе"),
    only_active: bool | None = Query(None, description="Только активные"),
):
    """
    Получить список блюд с фильтрацией, поиском и пагинацией.
    """
    total, items = await dish_crud.get_multi(
        session,
        limit=limit,
        offset=offset,
        q=q,
        cafe_id=cafe_id,
        only_active=only_active,
    )
    out_items = [
        DishOut(
            id=it.id,
            name=it.name,
            description=it.description,
            price=it.price,
            photo=it.photo,
            active=it.is_active,
            cafe_ids=[c.id for c in it.cafes],
        )
        for it in items
    ]
    return DishList(total=total, items=out_items)


@router.get("/active", response_model=DishList)
async def list_active_dishes(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: str | None = Query(None),
    cafe_id: int | None = Query(None),
):
    """
    Получить только активные блюда (короткая версия эндпоинта /dishes).
    """
    total, items = await dish_crud.get_multi(
        session,
        limit=limit,
        offset=offset,
        q=q,
        cafe_id=cafe_id,
        only_active=True,
    )
    out_items = [
        DishOut(
            id=it.id,
            name=it.name,
            description=it.description,
            price=it.price,
            photo=it.photo,
            active=it.is_active,
            cafe_ids=[c.id for c in it.cafes],
        )
        for it in items
    ]
    return DishList(total=total, items=out_items)


@router.get("/{dish_id}", response_model=DishOut)
async def get_dish(
    dish_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Получить детальную информацию о блюде по ID."""
    dish = await dish_crud.get(session, dish_id)
    if not dish:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Dish not found")
    return DishOut(
        id=dish.id,
        name=dish.name,
        description=dish.description,
        price=dish.price,
        photo=dish.photo,
        active=dish.is_active,
        cafe_ids=[c.id for c in dish.cafes],
    )


@router.post("/", response_model=DishOut, status_code=status.HTTP_201_CREATED)
async def create_dish(
    data: DishCreate,
    session: AsyncSession = Depends(get_session),
):
    """Создать новое блюдо."""
    dish = await dish_crud.create(
        session,
        name=data.name,
        description=data.description,
        price=data.price,
        photo=data.photo,
        cafe_ids=data.cafe_ids,
    )
    await session.commit()
    await session.refresh(dish)
    return DishOut(
        id=dish.id,
        name=dish.name,
        description=dish.description,
        price=dish.price,
        photo=dish.photo,
        active=dish.is_active,
        cafe_ids=[c.id for c in dish.cafes],
    )


@router.patch("/{dish_id}", response_model=DishOut)
async def update_dish(
    dish_id: int,
    data: DishUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Обновить данные существующего блюда."""
    dish = await dish_crud.get(session, dish_id)
    if not dish:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Dish not found")

    dish = await dish_crud.update(
        session,
        dish,
        name=data.name,
        description=data.description,
        price=data.price,
        photo=data.photo,
        active=data.active,
        cafe_ids=data.cafe_ids,
    )
    await session.commit()
    await session.refresh(dish)
    return DishOut(
        id=dish.id,
        name=dish.name,
        description=dish.description,
        price=dish.price,
        photo=dish.photo,
        active=dish.is_active,
        cafe_ids=[c.id for c in dish.cafes],
    )


@router.delete("/{dish_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dish(
    dish_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Мягкое удаление блюда (деактивация)."""
    dish = await dish_crud.get(session, dish_id)
    if not dish:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Dish not found")
    await dish_crud.soft_delete(session, dish)
    await session.commit()
    return None
