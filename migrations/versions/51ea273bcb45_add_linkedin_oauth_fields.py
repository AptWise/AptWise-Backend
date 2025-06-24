"""add linkedin oauth fields

Revision ID: 51ea273bcb45
Revises: d84e51d727ea
Create Date: 2025-06-21 13:53:55.091873

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51ea273bcb45'
down_revision: Union[str, Sequence[str], None] = 'd84e51d727ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add LinkedIn OAuth fields to users table
    op.add_column('users', sa.Column('linkedin_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('linkedin_access_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('profile_picture_url', sa.String(), nullable=True))
    op.add_column('users', sa.Column('is_linkedin_connected', sa.Boolean(), nullable=False, server_default='false'))
    
    # Create unique constraint on linkedin_id (when not null)
    op.create_index('ix_users_linkedin_id', 'users', ['linkedin_id'], unique=True, postgresql_where=sa.text('linkedin_id IS NOT NULL'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove LinkedIn OAuth fields
    op.drop_index('ix_users_linkedin_id', table_name='users')
    op.drop_column('users', 'is_linkedin_connected')
    op.drop_column('users', 'profile_picture_url')
    op.drop_column('users', 'linkedin_access_token')
    op.drop_column('users', 'linkedin_id')
