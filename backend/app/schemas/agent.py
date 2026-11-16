"""Agent Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, HttpUrl


class AgentRegister(BaseModel):
    """Schema for registering a new agent."""

    company_name: str
    industry_category: str
    webhook_url: str
    interest_manifesto: str


class AgentResponse(BaseModel):
    """Schema for agent responses."""

    id: UUID
    company_name: str
    industry_category: str
    webhook_url: str
    interest_manifesto: str
    trust_score: float
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentUpdate(BaseModel):
    """Schema for updating an agent — all fields optional."""

    company_name: Optional[str] = None
    industry_category: Optional[str] = None
    webhook_url: Optional[str] = None
    interest_manifesto: Optional[str] = None
    is_active: Optional[bool] = None
