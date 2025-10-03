from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.models.dish import Dish
from src.schemas.dish import DishCreate, DishOut, DishUpdate

router = APIRouter(prefix="/dishes", tags=["dishes"])


@router.post("/", response_model=DishOut)
async def create_dish(
    data: DishCreate,
    session: AsyncSession = Depends(get_session),
) -> DishOut:
    """Создать новое блюдо."""
    dish = Dish(**data.dict())
    session.add(dish)
    await session.commit()
    await session.refresh(dish)
    return dish


@router.get("/", response_model=list[DishOut])
async def list_dishes(
    session: AsyncSession = Depends(get_session),
    cafe_id: int | None = Query(None),
    q: str | None = Query(None),
    min_price: Decimal | None = Query(None, ge=0),
    max_price: Decimal | None = Query(None, ge=0),
    available: bool | None = Query(None),
    active: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
) -> list[DishOut]:
    """Список блюд с фильтрами по кафе, названию, цене и доступности."""
    stmt = select(Dish)
    if cafe_id is not None:
        stmt = stmt.where(Dish.cafe_id == cafe_id)
    if q:
        stmt = stmt.where(Dish.name.ilike(f"%{q}%"))
    if min_price is not None:
        stmt = stmt.where(Dish.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Dish.price <= max_price)
    if available is not None:
        stmt = stmt.where(Dish.is_available == available)
    if active is not None:
        stmt = stmt.where(Dish.active == active)

    res = await session.execute(stmt.offset(skip).limit(limit))
    return list(res.scalars())


@router.get("/{dish_id}", response_model=DishOut)
async def get_dish(
    dish_id: int,
    session: AsyncSession = Depends(get_session),
) -> DishOut:
    """Получить блюдо по ID."""
    dish = await session.get(Dish, dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")
    return dish


@router.patch("/{dish_id}", response_model=DishOut)
async def update_dish(
    dish_id: int,
    data: DishUpdate,
    session: AsyncSession = Depends(get_session),
) -> DishOut:
    """Частично обновить блюдо по ID."""
    dish = await session.get(Dish, dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")

    for k, v in data.dict(exclude_unset=True).items():
        setattr(dish, k, v)

    await session.commit()
    await session.refresh(dish)
    return dish


@router.delete("/{dish_id}", status_code=204)
async def delete_dish(
    dish_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Мягкое удаление блюда (active=False)."""
    dish = await session.get(Dish, dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")

    dish.active = False
    await session.commit()
