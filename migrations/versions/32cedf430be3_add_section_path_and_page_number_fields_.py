"""Add section_path and page_number fields to Chunk model

Revision ID: 32cedf430be3
Revises: 7468fa8fd0b2
Create Date: 2026-09-02 02:35:33.569992

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '32cedf430be3'
down_revision: Union[str, Sequence[str], None] = '7468fa8fd0b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('chunks', sa.Column('section_path', sa.JSON(), nullable=True))
    op.add_column('chunks', sa.Column('page_number', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('chunks', 'page_number')
    op.drop_column('chunks', 'section_path')
