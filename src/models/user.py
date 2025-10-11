from sqlalchemy import (
    CheckConstraint,
    Column,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from core.constants import (
    CK_USERS_CONTACT_REQUIRED,
    EMAIL_MAX,
    PASSWORD_HASH_MAX,
    PHONE_MAX,
    TG_ID_MAX,
    USERNAME_MAX,
)
from schemas.user import UserRole

from .base import BaseModel
from .relations import cafe_managers


class User(BaseModel):
    """ORM-модель пользователя (classic Column API)."""

    __tablename__ = 'users'
    __table_args__ = (
        # обязательно указан email ИЛИ phone
        CheckConstraint(
            '(email IS NOT NULL) OR (phone IS NOT NULL)',
            name=CK_USERS_CONTACT_REQUIRED,
        ),
    )

    username = Column(String(USERNAME_MAX), nullable=False)
    email = Column(String(EMAIL_MAX), nullable=True)
    phone = Column(String(PHONE_MAX), nullable=True)
    tg_id = Column(String(TG_ID_MAX), nullable=True)
    role = Column(Integer, nullable=False, default=int(UserRole.USER))
    password_hash = Column(String(PASSWORD_HASH_MAX), nullable=False)

    # many-to-many с кафе
    managed_cafes = relationship(
        'Cafe',
        secondary=cafe_managers,
        back_populates='managers',
        lazy='selectin',
    )

    # связь с Booking
    bookings = relationship(
        'Booking',
        back_populates='user',
        lazy='selectin',
    )
