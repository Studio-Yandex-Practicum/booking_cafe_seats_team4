from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Единая базовая модель проекта."""

    pass


from app.models.user import User  # noqa: F401,E402
