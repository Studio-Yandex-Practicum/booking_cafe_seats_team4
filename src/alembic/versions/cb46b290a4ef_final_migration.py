"""final migration.

Revision ID: cb46b290a4ef
Revises: 74b29fb4b37f
Create Date: 2025-10-23 11:45:37.693288
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'cb46b290a4ef'
down_revision: Union[str, Sequence[str], None] = '74b29fb4b37f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM dishes WHERE length(name) > 50
            ) THEN
                RAISE EXCEPTION
                'dishes.name has values longer than 50 chars. '
                'Shorten them before migration.';
            END IF;
        END $$;
        """
    )

    op.alter_column(
        'dishes',
        'name',
        existing_type=sa.VARCHAR(length=200),
        type_=sa.String(length=50),
        existing_nullable=False,
    )

    op.alter_column(
        'dishes',
        'price',
        existing_type=sa.NUMERIC(precision=10, scale=2),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using='round(price)::integer',
    )

    # убрать FK и колонки
    op.drop_constraint(
        op.f('dishes_cafe_id_fkey'),
        'dishes',
        type_='foreignkey',
    )
    op.drop_column('dishes', 'cafe_id')
    op.drop_column('dishes', 'is_available')


def downgrade() -> None:
    """Downgrade schema."""

    op.add_column(
        'dishes',
        sa.Column('is_available', sa.BOOLEAN(), nullable=False),
    )
    op.add_column(
        'dishes',
        sa.Column('cafe_id', sa.INTEGER(), nullable=False),
    )
    op.create_foreign_key(
        op.f('dishes_cafe_id_fkey'),
        'dishes',
        'cafes',
        ['cafe_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.alter_column(
        'dishes',
        'price',
        existing_type=sa.Integer(),
        type_=sa.NUMERIC(precision=10, scale=2),
        existing_nullable=False,
    )
    op.alter_column(
        'dishes',
        'name',
        existing_type=sa.String(length=50),
        type_=sa.VARCHAR(length=200),
        existing_nullable=False,
    )
