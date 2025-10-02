from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Единая базовая модель проекта."""

    pass


from app.users.models import User  # noqa: E402,F401
