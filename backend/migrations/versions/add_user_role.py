"""Add role column to users table

Revision ID: add_user_role
Revises: bb38887b5a46
Create Date: 2024-02-27 10:00:00.000000

Requirements: 15.3
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_user_role'
down_revision = 'bb38887b5a46'
branch_labels = None
depends_on = None


def upgrade():
    """Add role column to users table."""
    # Create enum type for user roles
    op.execute("CREATE TYPE userrole AS ENUM ('citizen', 'officer', 'admin')")
    
    # Add role column with default value 'citizen'
    op.add_column('users', sa.Column('role', sa.Enum('CITIZEN', 'OFFICER', 'ADMIN', name='userrole'), nullable=False, server_default='citizen'))


def downgrade():
    """Remove role column from users table."""
    op.drop_column('users', 'role')
    op.execute("DROP TYPE userrole")
