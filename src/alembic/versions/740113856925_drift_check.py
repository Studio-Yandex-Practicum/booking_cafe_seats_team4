"""drift check.

Revision ID: 740113856925
Revises: 901d1b91c52e
Create Date: 2025-10-17 12:29:36.463616
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision: str = "740113856925"
down_revision: Union[str, Sequence[str], None] = "901d1b91c52e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='dishes' AND column_name='media_id'
            ) THEN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='dishes' AND column_name='photo_id'
                ) THEN
                    ALTER TABLE dishes ADD COLUMN photo_id UUID;
                END IF;
                UPDATE dishes SET photo_id = media_id WHERE photo_id IS NULL;
                ALTER TABLE dishes DROP COLUMN media_id;
            ELSE
                -- Если media_id уже нет, просто удостоверимся, что photo_id есть
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='dishes' AND column_name='photo_id'
                ) THEN
                    ALTER TABLE dishes ADD COLUMN photo_id UUID;
                END IF;
            END IF;
        END$$;
        """
    )

    op.alter_column("dishes", "photo_id", existing_type=pg.UUID(), nullable=False)

    op.execute("UPDATE tables SET description = '' WHERE description IS NULL;")
    op.alter_column(
        "tables",
        "description",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column(
        "tables",
        "description",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )

    op.execute(
        """
        ALTER TABLE dishes ADD COLUMN IF NOT EXISTS media_id UUID;
        UPDATE dishes SET media_id = photo_id WHERE photo_id IS NOT NULL;
        ALTER TABLE dishes DROP COLUMN IF EXISTS photo_id;
        """
    )
