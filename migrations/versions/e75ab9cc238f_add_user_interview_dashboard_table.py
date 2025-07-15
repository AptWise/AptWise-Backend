"""add user interview dashboard table

Revision ID: e75ab9cc238f
Revises: 5eda92bf16c7
Create Date: 2025-07-15 12:40:56.384981

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e75ab9cc238f'
down_revision: Union[str, Sequence[str], None] = '5eda92bf16c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'user_interview_presets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('preset_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('company', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=255), nullable=True),
        sa.Column('skills', sa.ARRAY(sa.String()), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['email'], ['users.email'], ondelete='CASCADE')
    )
    
    # Add index for better performance on array queries
    op.create_index('idx_user_interview_presets_skills', 'user_interview_presets', ['skills'], postgresql_using='gin')
    op.create_index('idx_user_interview_presets_email', 'user_interview_presets', ['email'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_user_interview_presets_email', table_name='user_interview_presets')
    op.drop_index('idx_user_interview_presets_skills', table_name='user_interview_presets')
    op.drop_table('user_interview_presets')
