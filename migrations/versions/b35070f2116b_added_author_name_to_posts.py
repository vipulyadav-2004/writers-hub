"""Added author_name to posts

Revision ID: b35070f2116b
Revises: 
Create Date: 2024-01-18 22:15:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b35070f2116b'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # We use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('post', schema=None) as batch_op:
        # We add 'server_default' so existing rows get a value
        batch_op.add_column(sa.Column('author_name', sa.String(length=100), nullable=False, server_default='Unknown'))

def downgrade():
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.drop_column('author_name')