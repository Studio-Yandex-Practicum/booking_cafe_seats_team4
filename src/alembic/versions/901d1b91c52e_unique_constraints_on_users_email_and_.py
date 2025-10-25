"""unique constraints on users.email and users.phone.

Revision ID: 901d1b91c52e
Revises: fd63ee30f3be
Create Date: 2025-10-14 19:10:35.210512
"""
from typing import Sequence, Union

import sqlalchemy as sa  # noqa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "901d1b91c52e"
down_revision: Union[str, Sequence[str], None] = "fd63ee30f3be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute("UPDATE users SET email = BTRIM(email) WHERE email IS NOT NULL;")
    op.execute("UPDATE users SET phone = BTRIM(phone) WHERE phone IS NOT NULL;")

    op.execute("UPDATE users SET email = NULL WHERE email = '' OR email IS NULL;")
    op.execute("UPDATE users SET phone = NULL WHERE phone = '' OR phone IS NULL;")


    op.execute(
        """
        WITH d AS (
            SELECT id,
                   ROW_NUMBER() OVER (PARTITION BY email ORDER BY id) AS rn
            FROM users
            WHERE email IS NOT NULL
        )
        UPDATE users u
        SET email = NULL
        FROM d
        WHERE u.id = d.id AND d.rn > 1;
        """
    )

    op.execute(
        """
        WITH d AS (
            SELECT id,
                   ROW_NUMBER() OVER (PARTITION BY phone ORDER BY id) AS rn
            FROM users
            WHERE phone IS NOT NULL
        )
        UPDATE users u
        SET phone = NULL
        FROM d
        WHERE u.id = d.id AND d.rn > 1;
        """
    )

    op.create_unique_constraint("uq_users_email", "users", ["email"])
    op.create_unique_constraint("uq_users_phone", "users", ["phone"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_users_phone", "users", type_="unique")
    op.drop_constraint("uq_users_email", "users", type_="unique")
