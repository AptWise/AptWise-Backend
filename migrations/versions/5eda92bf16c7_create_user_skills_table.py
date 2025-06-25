"""Create user skills Table

Revision ID: 5eda92bf16c7
Revises: e6fcb89449b6
Create Date: 2025-06-25 18:31:19.248822

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5eda92bf16c7'
down_revision: Union[str, Sequence[str], None] = 'e6fcb89449b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'user_skills',
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('skill', sa.String(), nullable=False),
        sa.Column('proficiency', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['email'], ['users.email'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('email', 'skill')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('user_skills')
