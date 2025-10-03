from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Единая базовая модель проекта."""

    pass


# региструем модели в метадата
from models.cafe import Cafe  # noqa: F401,E402
from models.user import User  # noqa: F401,E402
