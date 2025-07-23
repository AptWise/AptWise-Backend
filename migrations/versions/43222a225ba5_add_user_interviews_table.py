"""add user interviews table

Revision ID: 43222a225ba5
Revises: e75ab9cc238f
Create Date: 2025-07-23 12:00:27.451395

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43222a225ba5'
down_revision: Union[str, Sequence[str], None] = 'e75ab9cc238f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('user_interviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('interview_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['email'], ['users.email'], ondelete='CASCADE')
    )
    
    # Create index on email for faster queries
    op.create_index(op.f('ix_user_interviews_email'), 'user_interviews', ['email'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index first
    op.drop_index(op.f('ix_user_interviews_email'), table_name='user_interviews')
    
    # Drop table
    op.drop_table('user_interviews')
