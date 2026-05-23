"""Initial migration

Revision ID: 56feea2e19a3
Revises: 
Create Date: 2026-05-23 18:01:44.343284

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '56feea2e19a3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'garments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('link', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('gender', sa.String(), nullable=True),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('fabric', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('sizes_stock', sa.JSON(), nullable=True),
        sa.Column('images', sa.JSON(), nullable=True),
        sa.Column('metadata_field', sa.JSON(), nullable=True),
        sa.Column('scraped_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_garments_id'), 'garments', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_garments_id'), table_name='garments')
    op.drop_table('garments')
