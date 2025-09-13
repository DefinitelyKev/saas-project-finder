from sqlalchemy import Column, String, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.infrastructure.database.base import TenantBaseModel
import enum


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectType(str, enum.Enum):
    SAAS = "saas"
    API = "api"
    WEBAPP = "webapp"
    MOBILE = "mobile"
    DESKTOP = "desktop"


class Project(TenantBaseModel):
    __tablename__ = "projects"
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    project_type = Column(Enum(ProjectType), nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False)
    
    # Configuration
    config = Column(JSON, default=dict, nullable=False)
    tech_stack = Column(JSON, default=list, nullable=False)
    requirements = Column(JSON, default=list, nullable=False)
    
    # Repository information
    repository_url = Column(String(500), nullable=True)
    deployment_url = Column(String(500), nullable=True)
    
    # Relationships
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="projects")
    ai_sessions = relationship("AISession", back_populates="project", cascade="all, delete-orphan")


class AISession(TenantBaseModel):
    __tablename__ = "ai_sessions"
    
    title = Column(String(500), nullable=False)
    objective = Column(Text, nullable=True)
    context = Column(JSON, default=dict, nullable=False)
    
    # AI Configuration
    model_config = Column(JSON, default=dict, nullable=False)
    tools_enabled = Column(JSON, default=list, nullable=False)
    
    # Results
    outputs = Column(JSON, default=list, nullable=False)
    metrics = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    user = relationship("User", back_populates="ai_sessions")
    project = relationship("Project", back_populates="ai_sessions")
    messages = relationship("AIMessage", back_populates="session", cascade="all, delete-orphan")


class AIMessage(TenantBaseModel):
    __tablename__ = "ai_messages"
    
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    metadata = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    session_id = Column(String, ForeignKey("ai_sessions.id"), nullable=False)
    session = relationship("AISession", back_populates="messages")