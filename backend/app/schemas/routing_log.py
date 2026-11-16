"""RoutingLog Pydantic schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RoutingLogResponse(BaseModel):
    """Schema for routing log responses."""

    id: UUID
    post_id: UUID
    target_agent_id: UUID
    vector_score: float
    rerank_score: float
    status: str
    created_at: datetime
    target_company_name: str = ""

    model_config = ConfigDict(from_attributes=True)
