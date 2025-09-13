from typing import Any
from sqlalchemy import Column, DateTime, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid


Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


class TenantBaseModel(BaseModel):
    """Base model for tenant-specific tables"""
    __abstract__ = True
    
    tenant_id = Column(String, nullable=False, index=True)
    
    @classmethod
    def get_table_name(cls, tenant_id: str) -> str:
        """Generate tenant-specific table name"""
        base_name = cls.__tablename__
        return f"{tenant_id}_{base_name}"