"""add m1 specific fields

Revision ID: a4b5c6d7e8f9
Revises: 93f73f15bcc1
Create Date: 2024-02-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = 'a4b5c6d7e8f9'
down_revision = '93f73f15bcc1'
branch_labels = None
depends_on = None

def upgrade():
    # Update TripStatus enum
    op.execute("ALTER TYPE tripstatus ADD VALUE 'IN_PROGRESS' AFTER 'CONFIRMED'")
    
    # Add M1-specific columns
    op.add_column('trips', sa.Column('m1_context', sa.JSON(), nullable=True, 
                                   comment='Stores M1-specific context and state'))
    op.add_column('trips', sa.Column('m1_monitoring', sa.JSON(), nullable=True,
                                   comment='Real-time monitoring configuration'))
    op.add_column('trips', sa.Column('m1_enabled', sa.Boolean(), nullable=False,
                                   server_default='true',
                                   comment='Whether M1 features are enabled'))
    op.add_column('trips', sa.Column('last_monitored', sa.DateTime(), nullable=True,
                                   comment='Last monitoring timestamp'))
    op.add_column('trips', sa.Column('monitoring_interval', sa.Numeric(10, 0), nullable=True,
                                   comment='Monitoring interval in seconds'))
    
    # Set default values for JSON columns
    op.execute("UPDATE trips SET m1_context = '{}' WHERE m1_context IS NULL")
    op.execute("UPDATE trips SET m1_monitoring = '{}' WHERE m1_monitoring IS NULL")
    
    # Make JSON columns non-nullable after setting defaults
    op.alter_column('trips', 'm1_context',
                    existing_type=sa.JSON(),
                    nullable=False,
                    server_default='{}')
    op.alter_column('trips', 'm1_monitoring',
                    existing_type=sa.JSON(),
                    nullable=False,
                    server_default='{}')

def downgrade():
    # Remove M1-specific columns
    op.drop_column('trips', 'monitoring_interval')
    op.drop_column('trips', 'last_monitored')
    op.drop_column('trips', 'm1_enabled')
    op.drop_column('trips', 'm1_monitoring')
    op.drop_column('trips', 'm1_context')
    
    # Remove in_progress from TripStatus enum
    # Note: This is a potentially dangerous operation if any trips are using this status
    op.execute("ALTER TYPE tripstatus DROP VALUE 'IN_PROGRESS'") 