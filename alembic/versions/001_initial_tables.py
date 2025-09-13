"""Initial tables

Revision ID: 001_initial_tables
Revises:
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tenants table
    op.create_table('tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('api_key_hash', sa.String(length=255), nullable=False),
        sa.Column('tier', sa.String(length=50), nullable=False, default='free'),
        sa.Column('allowed_agents', sa.JSON(), nullable=False, default=[]),
        sa.Column('monthly_tokens_used', sa.Integer(), nullable=False, default=0),
        sa.Column('current_month', sa.String(length=7), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('api_key_hash')
    )

    # Create agents table
    op.create_table('agents',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('model', sa.String(length=50), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('tools', sa.JSON(), nullable=False, default=[]),
        sa.Column('parameters_schema', sa.JSON(), nullable=False, default={}),
        sa.Column('max_tokens', sa.Integer(), nullable=False, default=1000),
        sa.Column('temperature', sa.Float(), nullable=False, default=0.7),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('total_executions', sa.Integer(), nullable=False, default=0),
        sa.Column('total_tokens_used', sa.Integer(), nullable=False, default=0),
        sa.Column('success_rate', sa.Float(), nullable=False, default=0.0),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Create executions table
    op.create_table('executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(length=100), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, default='pending'),
        sa.Column('input_parameters', sa.JSON(), nullable=False, default={}),
        sa.Column('result', sa.JSON(), nullable=False, default={}),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('token_usage', sa.Integer(), nullable=False, default=0),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'])
    )

    # Create sessions table
    op.create_table('sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(length=100), nullable=False),
        sa.Column('messages', sa.JSON(), nullable=False, default=[]),
        sa.Column('session_metadata', sa.JSON(), nullable=False, default={}),
        sa.Column('total_tokens_used', sa.Integer(), nullable=False, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('last_activity', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'])
    )

    # Create usage_logs table
    op.create_table('usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(length=100), nullable=False),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=False, default=0),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False, default=0),
        sa.Column('success', sa.Boolean(), nullable=False, default=True),
        sa.Column('error_type', sa.String(length=100), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id']),
        sa.ForeignKeyConstraint(['execution_id'], ['executions.id'])
    )

    # Create indexes
    op.create_index('idx_tenants_api_key', 'tenants', ['api_key_hash'])
    op.create_index('idx_executions_tenant_agent', 'executions', ['tenant_id', 'agent_id'])
    op.create_index('idx_executions_status_created', 'executions', ['status', 'created_at'])
    op.create_index('idx_sessions_tenant_active', 'sessions', ['tenant_id', 'is_active'])
    op.create_index('idx_usage_logs_tenant_timestamp', 'usage_logs', ['tenant_id', 'timestamp'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_usage_logs_tenant_timestamp', table_name='usage_logs')
    op.drop_index('idx_sessions_tenant_active', table_name='sessions')
    op.drop_index('idx_executions_status_created', table_name='executions')
    op.drop_index('idx_executions_tenant_agent', table_name='executions')
    op.drop_index('idx_tenants_api_key', table_name='tenants')

    # Drop tables in reverse order
    op.drop_table('usage_logs')
    op.drop_table('sessions')
    op.drop_table('executions')
    op.drop_table('agents')
    op.drop_table('tenants')