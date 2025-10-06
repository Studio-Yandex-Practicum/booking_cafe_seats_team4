"""sync classic Column API."""

from typing import Sequence, Union

import sqlalchemy as sa  # noqa: F401

from alembic import op

revision: str = '2d5ac182234c'
down_revision: Union[str, Sequence[str], None] = '740679b7ecd8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema (idempotent)."""
    # UQ (cafe_id, user_id): если индекса/констрейнта нет —
    # создаём
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_class
                WHERE relname = 'uq_cafe_manager_cafe_user'
                  AND relkind = 'i'
            ) THEN
                CREATE UNIQUE INDEX uq_cafe_manager_cafe_user
                    ON cafe_manager (cafe_id, user_id);
            END IF;

            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_cafe_manager_cafe_user'
            ) THEN
                ALTER TABLE cafe_manager
                    ADD CONSTRAINT uq_cafe_manager_cafe_user
                    UNIQUE USING INDEX uq_cafe_manager_cafe_user;
            END IF;
        END $$;
        """,
    )

    # FKs: если нет — добавляем
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_cafe_manager_user_id_users'
            ) THEN
                ALTER TABLE cafe_manager
                    ADD CONSTRAINT fk_cafe_manager_user_id_users
                    FOREIGN KEY (user_id)
                    REFERENCES users (id)
                    ON DELETE CASCADE;
            END IF;

            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_cafe_manager_cafe_id_cafes'
            ) THEN
                ALTER TABLE cafe_manager
                    ADD CONSTRAINT fk_cafe_manager_cafe_id_cafes
                    FOREIGN KEY (cafe_id)
                    REFERENCES cafes (id)
                    ON DELETE CASCADE;
            END IF;
        END $$;
        """,
    )


def downgrade() -> None:
    """Downgrade schema (idempotent)."""
    op.execute(
        """
        ALTER TABLE cafe_manager
            DROP CONSTRAINT IF EXISTS fk_cafe_manager_cafe_id_cafes;
        ALTER TABLE cafe_manager
            DROP CONSTRAINT IF EXISTS fk_cafe_manager_user_id_users;

        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_cafe_manager_cafe_user'
            ) THEN
                ALTER TABLE cafe_manager
                    DROP CONSTRAINT uq_cafe_manager_cafe_user;
            END IF;

            IF EXISTS (
                SELECT 1
                FROM pg_class
                WHERE relname = 'uq_cafe_manager_cafe_user'
                  AND relkind = 'i'
            ) THEN
                DROP INDEX uq_cafe_manager_cafe_user;
            END IF;
        END $$;
        """,
    )
