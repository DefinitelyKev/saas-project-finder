from sqlalchemy import Column, String, Text, Boolean, JSON, Integer
from app.infrastructure.database.base import BaseModel


class Tenant(BaseModel):
    __tablename__ = "tenants"
    
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    domain = Column(String(255), unique=True, nullable=True)
    database_url = Column(Text, nullable=True)  # For database-per-tenant strategy
    
    # Plan and limits
    plan_type = Column(String(50), default="free", nullable=False)
    api_rate_limit = Column(Integer, default=100, nullable=False)
    storage_limit_gb = Column(Integer, default=1, nullable=False)
    
    # Features
    features = Column(JSON, default=dict, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    settings = Column(JSON, default=dict, nullable=False)
    metadata = Column(JSON, default=dict, nullable=False)