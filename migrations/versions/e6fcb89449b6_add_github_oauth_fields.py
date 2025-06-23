"""add github oauth fields

Revision ID: e6fcb89449b6
Revises: 51ea273bcb45
Create Date: 2025-06-23 09:11:43.458320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6fcb89449b6'
down_revision: Union[str, Sequence[str], None] = '51ea273bcb45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add GitHub OAuth fields to users table
    op.add_column('users', sa.Column('github_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('github_access_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('is_github_connected', sa.Boolean(), nullable=False, server_default='false'))
    
    # Create unique constraint on github_id (when not null)
    op.create_index('ix_users_github_id', 'users', ['github_id'], unique=True, postgresql_where=sa.text('github_id IS NOT NULL'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove GitHub OAuth fields
    op.drop_index('ix_users_github_id', table_name='users')
    op.drop_column('users', 'is_github_connected')
    op.drop_column('users', 'github_access_token')
    op.drop_column('users', 'github_id')
