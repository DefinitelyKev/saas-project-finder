from datetime import datetime, date
from typing import Dict, Any, List, Optional
from uuid import uuid4
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, JSON, Date, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.database import Base


class TenantModel(Base):
    """SQLAlchemy model for tenants."""

    __tablename__ = "tenants"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    tier: Mapped[str] = mapped_column(String(50), nullable=False, default="free")
    allowed_agents: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    monthly_tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_month: Mapped[str] = mapped_column(String(7), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class AgentModel(Base):
    """SQLAlchemy model for agents."""

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    tools: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=list)
    parameters_schema: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    total_executions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class ExecutionModel(Base):
    """SQLAlchemy model for executions."""

    __tablename__ = "executions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    session_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    input_parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    result: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    token_usage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    execution_time_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class SessionModel(Base):
    """SQLAlchemy model for sessions."""

    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    messages: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=list)
    session_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    total_tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    last_activity: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class UsageLogModel(Base):
    """SQLAlchemy model for usage logs."""

    __tablename__ = "usage_logs"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    execution_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    billing_period: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class SaaSProjectIdeaModel(Base):
    """SQLAlchemy model for SaaS project ideas."""

    __tablename__ = "saas_project_ideas"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_platform: Mapped[str] = mapped_column(String(50), nullable=False)  # producthunt, reddit, etc.

    # Scoring metrics
    trend_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 0-100
    market_potential_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 0-100
    ai_agent_suitability_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 0-100
    competition_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 0-100, higher = less competition
    implementation_difficulty: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")  # easy, medium, hard
    monetization_potential_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 0-100
    composite_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # Weighted final score

    # Market analysis
    estimated_market_size: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    competition_level: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")  # low, medium, high
    target_audience: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Ranking and tracking
    current_ranking_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    previous_ranking_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weekly_rank_change: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Timestamps and status
    discovered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    last_analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_ranked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Analysis and metadata
    analysis_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    tags: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    engagement_metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Indexes for performance
    __table_args__ = (
        Index('idx_saas_ideas_composite_score', 'composite_score'),
        Index('idx_saas_ideas_platform_date', 'source_platform', 'discovered_at'),
        Index('idx_saas_ideas_ranking', 'current_ranking_position'),
        Index('idx_saas_ideas_active', 'is_active'),
    )


class TrendingMetricsModel(Base):
    """SQLAlchemy model for tracking trending metrics over time."""

    __tablename__ = "trending_metrics"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_idea_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # producthunt, reddit, twitter, etc.

    # Engagement metrics
    mentions_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    engagement_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    growth_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # percentage growth
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # -1 to 1

    # Platform-specific metrics
    platform_specific_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Indexes for performance
    __table_args__ = (
        Index('idx_trending_metrics_project_platform', 'project_idea_id', 'platform'),
        Index('idx_trending_metrics_timestamp', 'timestamp'),
        Index('idx_trending_metrics_engagement', 'engagement_score'),
    )


class WeeklyReportModel(Base):
    """SQLAlchemy model for weekly SaaS idea reports."""

    __tablename__ = "weekly_reports"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)

    # Report content
    top_ideas: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    market_insights: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    trending_categories: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)

    # Report metadata
    total_ideas_analyzed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_ideas_discovered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Email delivery tracking
    recipient_emails: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivery_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending, sent, failed

    # Timestamps
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Indexes for performance
    __table_args__ = (
        Index('idx_weekly_reports_week', 'week_start', 'week_end'),
        Index('idx_weekly_reports_status', 'delivery_status'),
    )


class SaaSIdeaAnalysisLogModel(Base):
    """SQLAlchemy model for logging analysis results and agent executions."""

    __tablename__ = "saas_idea_analysis_logs"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_idea_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False)  # scanner, analyzer, ranker
    analysis_type: Mapped[str] = mapped_column(String(50), nullable=False)  # discovery, analysis, ranking

    # Analysis results
    input_parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    analysis_results: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    scores_generated: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Execution metadata
    execution_time_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Indexes for performance
    __table_args__ = (
        Index('idx_analysis_logs_project_agent', 'project_idea_id', 'agent_id'),
        Index('idx_analysis_logs_type_date', 'analysis_type', 'created_at'),
    )