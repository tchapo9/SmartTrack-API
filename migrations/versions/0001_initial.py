"""Initial database schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-08-04 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('username', sa.String(length=50), nullable=False, unique=True, index=True),
        sa.Column('email', sa.String(length=100), nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('role', sa.Enum('USER', 'ADMIN', 'PREMIUM', name='userrole'), nullable=False, server_default='USER'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        'devices',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('device_name', sa.String(length=100), nullable=False),
        sa.Column('device_uuid', sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column('android_version', sa.String(length=20), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('battery_level', sa.Float(), nullable=True, server_default='0'),
        sa.Column('status', sa.Enum('online', 'offline', 'inactive', 'lost', name='devicestatus'), nullable=True, server_default='offline'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('last_connection', sa.DateTime(timezone=True), nullable=True),
        sa.Column('lost_mode', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        'locations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('device_id', sa.Integer(), sa.ForeignKey('devices.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('altitude', sa.Float(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('speed', sa.Float(), nullable=True),
        sa.Column('battery', sa.Float(), nullable=True),
        sa.Column('point', Geometry('POINT', srid=4326), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_locations_device_timestamp', 'locations', ['device_id', 'timestamp'])
    op.create_index('ix_locations_point', 'locations', ['point'], postgresql_using='gist')

    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('device_id', sa.Integer(), sa.ForeignKey('devices.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('type', sa.Enum('low_battery', 'geofence_exit', 'geofence_enter', 'device_offline', 'movement_detected', 'speed_exceeded', 'lost_mode', name='alerttype'), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('message', sa.String(length=500), nullable=False),
        sa.Column('status', sa.Enum('pending', 'read', 'resolved', name='alertstatus'), nullable=False, server_default='pending'),
        sa.Column('data', sa.String(length=500), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        'geofences',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('device_id', sa.Integer(), sa.ForeignKey('devices.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('radius', sa.Float(), nullable=False),
        sa.Column('point', Geometry('POINT', srid=4326), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_table('geofences')
    op.drop_table('alerts')
    op.drop_index('ix_locations_point', table_name='locations')
    op.drop_index('ix_locations_device_timestamp', table_name='locations')
    op.drop_table('locations')
    op.drop_table('devices')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS devicestatus')
    op.execute('DROP TYPE IF EXISTS alerttype')
    op.execute('DROP TYPE IF EXISTS alertstatus')
