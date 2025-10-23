from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password
from crud.base import CRUDBase
from models.user import User
from schemas.user import UserCreate, UserUpdate
from services.users import apply_user_update

from .base import audit_event


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD для пользователей с логикой пароля и флагов."""

    async def list_all(
        self,
        session: AsyncSession,
        only_active: bool = True,
    ) -> List[User]:
        """Вернуть всех пользователей, отсортированных по id."""
        stmt = select(User).order_by(User.id)
        if only_active and hasattr(User, 'is_active'):
            stmt = stmt.where(User.is_active.is_(True))
        res = await session.execute(stmt)
        return list(res.scalars().all())

    async def create_with_hash(
        self,
        obj_in: UserCreate,
        session: AsyncSession,
    ) -> User:
        """Создать пользователя: хеш пароля + дефолты."""
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            phone=obj_in.phone,
            tg_id=obj_in.tg_id,
            role=0,
            is_active=True,
            password_hash=hash_password(obj_in.password),
        )
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)

        audit_event('user', 'created', id=db_obj.id, role=db_obj.role)

        return db_obj

    async def update_with_logic(
        self,
        db_obj: User,
        obj_in: UserUpdate,
        session: AsyncSession,
    ) -> User:
        """Частичное обновление через apply_user_update."""
        apply_user_update(db_obj, obj_in)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)

        audit_event('user', 'updated', id=db_obj.id)

        return db_obj


user_crud = CRUDUser(User)
