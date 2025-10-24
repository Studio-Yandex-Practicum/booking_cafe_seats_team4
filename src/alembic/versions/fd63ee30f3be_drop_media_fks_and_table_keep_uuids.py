"""drop FKs to media and drop media table."""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "fd63ee30f3be"
down_revision: Union[str, Sequence[str], None] = "d03009fd0dd0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Снять FK с cafes.photo_id -> media.id
    op.execute(
        """
        DO $$
        DECLARE fkname text;
        BEGIN
            SELECT c.conname INTO fkname
            FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            WHERE t.relname = 'cafes'
              AND c.contype = 'f'
              AND pg_get_constraintdef(c.oid) ILIKE '%%REFERENCES media(%%';
            IF fkname IS NOT NULL THEN
                EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I', 'cafes', fkname);
            END IF;
        END$$ LANGUAGE plpgsql;
        """
    )

    # Снять FK с actions.photo_id -> media.id
    op.execute(
        """
        DO $$
        DECLARE fkname text;
        BEGIN
            SELECT c.conname INTO fkname
            FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            WHERE t.relname = 'actions'
              AND c.contype = 'f'
              AND pg_get_constraintdef(c.oid) ILIKE '%%REFERENCES media(%%';
            IF fkname IS NOT NULL THEN
                EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I', 'actions', fkname);
            END IF;
        END$$ LANGUAGE plpgsql;
        """
    )

    # Если таблица media есть - удаляем.
    op.execute("DROP TABLE IF EXISTS media;")


def downgrade() -> None:
    op.create_table(
        "media",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
    )
    op.create_foreign_key(
        "cafes_photo_id_fkey", "cafes", "media", ["photo_id"], ["id"]
    )
    op.create_foreign_key(
        "actions_photo_id_fkey", "actions", "media", ["photo_id"], ["id"]
    )
