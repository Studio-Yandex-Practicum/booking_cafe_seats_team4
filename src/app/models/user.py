from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    """ORM-модель пользователя."""

    __tablename__ = 'users'
    # требование: email ИЛИ phone обязательно
    __table_args__ = (
        CheckConstraint(
            '(email IS NOT NULL) OR (phone IS NOT NULL)',
            name='ck_users_contact_required',
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    username: Mapped[str] = mapped_column(String(150), nullable=False)

    # теперь опционльны на уровне БД
    email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    tg_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # enum 0/1/2 (по OpenAPI)
    role: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    is_active: Mapped[bool] = mapped_column(
        'active',
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
