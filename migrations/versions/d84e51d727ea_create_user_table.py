"""create user table

Revision ID: d84e51d727ea
Revises: 
Create Date: 2025-06-20 18:28:15.889630

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd84e51d727ea'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('email', sa.String(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('linkedin_url', sa.String(), nullable=True),
        sa.Column('github_url', sa.String(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('users')

