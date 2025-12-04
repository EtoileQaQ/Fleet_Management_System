"""Add telematics fields and driver_activities table

Revision ID: 002_telematics
Revises: 001_initial
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_telematics'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add real-time tracking fields to vehicles
    op.add_column('vehicles', sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True))
    op.add_column('vehicles', sa.Column('current_position', geoalchemy2.types.Geometry(
        geometry_type='POINT', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'
    ), nullable=True))
    op.add_column('vehicles', sa.Column('current_speed', sa.Float(), nullable=True))
    op.add_column('vehicles', sa.Column('current_heading', sa.Float(), nullable=True))
    op.add_column('vehicles', sa.Column('total_odometer', sa.Float(), nullable=True))
    op.create_index('ix_vehicles_last_seen', 'vehicles', ['last_seen'], unique=False)
    
    # Add card_number to drivers
    op.add_column('drivers', sa.Column('card_number', sa.String(length=50), nullable=True))
    op.create_index('ix_drivers_card_number', 'drivers', ['card_number'], unique=True)
    
    # Create activity type enum
    activitytype = postgresql.ENUM(
        'DRIVING', 'REST', 'WORK', 'AVAILABILITY', 'BREAK', 'UNKNOWN',
        name='activitytype', create_type=False
    )
    activitytype.create(op.get_bind(), checkfirst=True)
    
    # Create activity source enum
    activitysource = postgresql.ENUM(
        'TACHOGRAPH', 'MANUAL', 'GPS_INFERRED',
        name='activitysource', create_type=False
    )
    activitysource.create(op.get_bind(), checkfirst=True)
    
    # Create driver_activities table
    op.create_table(
        'driver_activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=True),
        sa.Column('activity_type', postgresql.ENUM(
            'DRIVING', 'REST', 'WORK', 'AVAILABILITY', 'BREAK', 'UNKNOWN',
            name='activitytype', create_type=False
        ), nullable=False),
        sa.Column('source', postgresql.ENUM(
            'TACHOGRAPH', 'MANUAL', 'GPS_INFERRED',
            name='activitysource', create_type=False
        ), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('odometer_start', sa.Float(), nullable=True),
        sa.Column('odometer_end', sa.Float(), nullable=True),
        sa.Column('distance_km', sa.Float(), nullable=True),
        sa.Column('source_file', sa.String(length=255), nullable=True),
        sa.Column('card_number', sa.String(length=50), nullable=True),
        sa.Column('raw_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_driver_activities_id', 'driver_activities', ['id'], unique=False)
    op.create_index('ix_driver_activities_driver_id', 'driver_activities', ['driver_id'], unique=False)
    op.create_index('ix_driver_activities_vehicle_id', 'driver_activities', ['vehicle_id'], unique=False)
    op.create_index('ix_driver_activities_activity_type', 'driver_activities', ['activity_type'], unique=False)
    op.create_index('ix_driver_activities_start_time', 'driver_activities', ['start_time'], unique=False)
    op.create_index('ix_driver_activities_end_time', 'driver_activities', ['end_time'], unique=False)
    op.create_index('idx_activity_driver_time', 'driver_activities', ['driver_id', 'start_time', 'end_time'], unique=False)
    op.create_index('idx_activity_time_range', 'driver_activities', ['start_time', 'end_time'], unique=False)
    op.create_index('idx_activity_card', 'driver_activities', ['card_number', 'start_time'], unique=False)


def downgrade() -> None:
    # Drop driver_activities
    op.drop_table('driver_activities')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS activitytype')
    op.execute('DROP TYPE IF EXISTS activitysource')
    
    # Remove columns from drivers
    op.drop_index('ix_drivers_card_number', table_name='drivers')
    op.drop_column('drivers', 'card_number')
    
    # Remove columns from vehicles
    op.drop_index('ix_vehicles_last_seen', table_name='vehicles')
    op.drop_column('vehicles', 'total_odometer')
    op.drop_column('vehicles', 'current_heading')
    op.drop_column('vehicles', 'current_speed')
    op.drop_column('vehicles', 'current_position')
    op.drop_column('vehicles', 'last_seen')


