from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from core.db import Base


class Media(Base):
    """ORM-модель медиа-файла: хранит UUID-идентификатор (PK)."""

    __tablename__ = 'media'

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
