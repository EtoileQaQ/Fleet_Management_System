"""Initial migration - Create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types first (with IF NOT EXISTS logic)
    userrole = postgresql.ENUM('ADMIN', 'RH', 'VIEWER', name='userrole', create_type=False)
    userrole.create(op.get_bind(), checkfirst=True)
    
    vehiclestatus = postgresql.ENUM('ACTIVE', 'MAINTENANCE', 'INACTIVE', name='vehiclestatus', create_type=False)
    vehiclestatus.create(op.get_bind(), checkfirst=True)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', userrole, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_id', 'users', ['id'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # Create vehicles table
    op.create_table(
        'vehicles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('registration_plate', sa.String(length=20), nullable=False),
        sa.Column('vin', sa.String(length=17), nullable=False),
        sa.Column('brand', sa.String(length=100), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('status', postgresql.ENUM('ACTIVE', 'MAINTENANCE', 'INACTIVE', name='vehiclestatus', create_type=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_vehicles_id', 'vehicles', ['id'], unique=False)
    op.create_index('ix_vehicles_registration_plate', 'vehicles', ['registration_plate'], unique=True)
    op.create_index('ix_vehicles_vin', 'vehicles', ['vin'], unique=True)
    
    # Create drivers table
    op.create_table(
        'drivers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('license_number', sa.String(length=50), nullable=False),
        sa.Column('rfid_tag', sa.String(length=100), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('current_vehicle_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['current_vehicle_id'], ['vehicles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_drivers_id', 'drivers', ['id'], unique=False)
    op.create_index('ix_drivers_license_number', 'drivers', ['license_number'], unique=True)
    op.create_index('ix_drivers_rfid_tag', 'drivers', ['rfid_tag'], unique=True)
    
    # Create gps_positions table with PostGIS geometry
    op.create_table(
        'gps_positions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=False),
        sa.Column('speed', sa.Float(), nullable=True),
        sa.Column('heading', sa.Float(), nullable=True),
        sa.Column('odometer', sa.Float(), nullable=True),
        sa.Column('ignition_status', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_gps_positions_id', 'gps_positions', ['id'], unique=False)
    op.create_index('ix_gps_positions_vehicle_id', 'gps_positions', ['vehicle_id'], unique=False)
    op.create_index('ix_gps_positions_driver_id', 'gps_positions', ['driver_id'], unique=False)
    op.create_index('ix_gps_positions_timestamp', 'gps_positions', ['timestamp'], unique=False)
    op.create_index('idx_gps_vehicle_timestamp', 'gps_positions', ['vehicle_id', 'timestamp'], unique=False)


def downgrade() -> None:
    op.drop_table('gps_positions')
    op.drop_table('drivers')
    op.drop_table('vehicles')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS vehiclestatus')

