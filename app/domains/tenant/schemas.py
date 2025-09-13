from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import re


class TenantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    domain: Optional[str] = Field(None, max_length=255)
    plan_type: str = Field(default="free", max_length=50)
    api_rate_limit: int = Field(default=100, ge=1)
    storage_limit_gb: int = Field(default=1, ge=1)
    features: Dict[str, Any] = Field(default_factory=dict)
    settings: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator("slug")
    def validate_slug(cls, v):
        if not re.match(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        return v
    
    @validator("domain")
    def validate_domain(cls, v):
        if v and not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$", v):
            raise ValueError("Invalid domain format")
        return v


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    plan_type: Optional[str] = Field(None, max_length=50)
    api_rate_limit: Optional[int] = Field(None, ge=1)
    storage_limit_gb: Optional[int] = Field(None, ge=1)
    features: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    
    @validator("domain")
    def validate_domain(cls, v):
        if v and not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$", v):
            raise ValueError("Invalid domain format")
        return v


class TenantResponse(TenantBase):
    id: str
    is_active: bool
    is_verified: bool
    is_deleted: bool
    created_at: str
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True