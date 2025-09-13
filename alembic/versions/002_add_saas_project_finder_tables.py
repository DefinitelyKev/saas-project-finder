"""Add SaaS Project Finder tables

Revision ID: 002_add_saas_project_finder_tables
Revises: 001_initial_tables
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_add_saas_project_finder_tables'
down_revision = '001_initial_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create saas_project_ideas table
    op.create_table('saas_project_ideas',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('source_url', sa.String(length=1000), nullable=False),
        sa.Column('source_platform', sa.String(length=50), nullable=False),

        # Scoring metrics
        sa.Column('trend_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('market_potential_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('ai_agent_suitability_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('competition_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('implementation_difficulty', sa.String(length=20), nullable=False, default='medium'),
        sa.Column('monetization_potential_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('composite_score', sa.Float(), nullable=False, default=0.0),

        # Market analysis
        sa.Column('estimated_market_size', sa.String(length=100), nullable=True),
        sa.Column('competition_level', sa.String(length=20), nullable=False, default='medium'),
        sa.Column('target_audience', sa.String(length=500), nullable=True),

        # Ranking and tracking
        sa.Column('current_ranking_position', sa.Integer(), nullable=True),
        sa.Column('previous_ranking_position', sa.Integer(), nullable=True),
        sa.Column('weekly_rank_change', sa.Integer(), nullable=False, default=0),

        # Timestamps and status
        sa.Column('discovered_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('last_analyzed_at', sa.DateTime(), nullable=True),
        sa.Column('last_ranked_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),

        # Analysis and metadata
        sa.Column('analysis_data', sa.JSON(), nullable=False, default={}),
        sa.Column('tags', sa.JSON(), nullable=False, default=[]),
        sa.Column('engagement_metrics', sa.JSON(), nullable=False, default={}),

        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for saas_project_ideas
    op.create_index('idx_saas_ideas_composite_score', 'saas_project_ideas', ['composite_score'])
    op.create_index('idx_saas_ideas_platform_date', 'saas_project_ideas', ['source_platform', 'discovered_at'])
    op.create_index('idx_saas_ideas_ranking', 'saas_project_ideas', ['current_ranking_position'])
    op.create_index('idx_saas_ideas_active', 'saas_project_ideas', ['is_active'])

    # Create trending_metrics table
    op.create_table('trending_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_idea_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),

        # Engagement metrics
        sa.Column('mentions_count', sa.Integer(), nullable=False, default=0),
        sa.Column('engagement_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('growth_rate', sa.Float(), nullable=False, default=0.0),
        sa.Column('sentiment_score', sa.Float(), nullable=False, default=0.0),

        # Platform-specific metrics
        sa.Column('platform_specific_data', sa.JSON(), nullable=False, default={}),

        # Timestamp
        sa.Column('timestamp', sa.DateTime(), nullable=False, default=sa.func.now()),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_idea_id'], ['saas_project_ideas.id'], ondelete='CASCADE')
    )

    # Create indexes for trending_metrics
    op.create_index('idx_trending_metrics_project_platform', 'trending_metrics', ['project_idea_id', 'platform'])
    op.create_index('idx_trending_metrics_timestamp', 'trending_metrics', ['timestamp'])
    op.create_index('idx_trending_metrics_engagement', 'trending_metrics', ['engagement_score'])

    # Create weekly_reports table
    op.create_table('weekly_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('week_start', sa.Date(), nullable=False),
        sa.Column('week_end', sa.Date(), nullable=False),

        # Report content
        sa.Column('top_ideas', sa.JSON(), nullable=False, default=[]),
        sa.Column('market_insights', sa.JSON(), nullable=False, default={}),
        sa.Column('trending_categories', sa.JSON(), nullable=False, default=[]),

        # Report metadata
        sa.Column('total_ideas_analyzed', sa.Integer(), nullable=False, default=0),
        sa.Column('new_ideas_discovered', sa.Integer(), nullable=False, default=0),

        # Email delivery tracking
        sa.Column('recipient_emails', sa.JSON(), nullable=False, default=[]),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivery_status', sa.String(length=20), nullable=False, default='pending'),

        # Timestamps
        sa.Column('generated_at', sa.DateTime(), nullable=False, default=sa.func.now()),

        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for weekly_reports
    op.create_index('idx_weekly_reports_week', 'weekly_reports', ['week_start', 'week_end'])
    op.create_index('idx_weekly_reports_status', 'weekly_reports', ['delivery_status'])

    # Create saas_idea_analysis_logs table
    op.create_table('saas_idea_analysis_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_idea_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(length=100), nullable=False),
        sa.Column('analysis_type', sa.String(length=50), nullable=False),

        # Analysis results
        sa.Column('input_parameters', sa.JSON(), nullable=False, default={}),
        sa.Column('analysis_results', sa.JSON(), nullable=False, default={}),
        sa.Column('scores_generated', sa.JSON(), nullable=False, default={}),

        # Execution metadata
        sa.Column('execution_time_ms', sa.Integer(), nullable=False, default=0),
        sa.Column('tokens_used', sa.Integer(), nullable=False, default=0),
        sa.Column('success', sa.Boolean(), nullable=False, default=True),
        sa.Column('error_message', sa.Text(), nullable=True),

        # Timestamp
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_idea_id'], ['saas_project_ideas.id'], ondelete='CASCADE')
    )

    # Create indexes for saas_idea_analysis_logs
    op.create_index('idx_analysis_logs_project_agent', 'saas_idea_analysis_logs', ['project_idea_id', 'agent_id'])
    op.create_index('idx_analysis_logs_type_date', 'saas_idea_analysis_logs', ['analysis_type', 'created_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('idx_analysis_logs_type_date', table_name='saas_idea_analysis_logs')
    op.drop_index('idx_analysis_logs_project_agent', table_name='saas_idea_analysis_logs')
    op.drop_table('saas_idea_analysis_logs')

    op.drop_index('idx_weekly_reports_status', table_name='weekly_reports')
    op.drop_index('idx_weekly_reports_week', table_name='weekly_reports')
    op.drop_table('weekly_reports')

    op.drop_index('idx_trending_metrics_engagement', table_name='trending_metrics')
    op.drop_index('idx_trending_metrics_timestamp', table_name='trending_metrics')
    op.drop_index('idx_trending_metrics_project_platform', table_name='trending_metrics')
    op.drop_table('trending_metrics')

    op.drop_index('idx_saas_ideas_active', table_name='saas_project_ideas')
    op.drop_index('idx_saas_ideas_ranking', table_name='saas_project_ideas')
    op.drop_index('idx_saas_ideas_platform_date', table_name='saas_project_ideas')
    op.drop_index('idx_saas_ideas_composite_score', table_name='saas_project_ideas')
    op.drop_table('saas_project_ideas')