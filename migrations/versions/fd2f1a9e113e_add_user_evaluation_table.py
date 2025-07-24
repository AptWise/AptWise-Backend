"""add user evaluation table

Revision ID: fd2f1a9e113e
Revises: 43222a225ba5
Create Date: 2025-07-23 12:27:06.114436

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd2f1a9e113e'
down_revision: Union[str, Sequence[str], None] = '43222a225ba5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'user_evaluation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('interview_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('evaluation_text', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['email'], ['users.email'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['interview_id'], ['user_interviews.id'], ondelete='CASCADE'),
    )
    # Create index on email for faster queries
    op.create_index(op.f('ix_user_evaluation_email'), 'user_evaluation', ['email'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index first
    op.drop_index(op.f('ix_user_evaluation_email'), table_name='user_evaluation')
    op.drop_table('user_evaluation')
