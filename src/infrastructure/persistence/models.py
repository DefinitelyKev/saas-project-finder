from datetime import datetime
from typing import Dict, Any, List
from uuid import uuid4
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, JSON
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
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
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