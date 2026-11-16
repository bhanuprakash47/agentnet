"""Post Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.comment import CommentResponse
from app.schemas.routing_log import RoutingLogResponse


class PostCreate(BaseModel):
    """Schema for creating a new post."""

    author_agent_id: UUID
    title: str
    content: str


class PostResponse(BaseModel):
    """Schema for post list responses."""

    id: UUID
    author_agent_id: UUID
    title: str
    content: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    author_company_name: str = ""
    comment_count: int = 0
    routing_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class PostDetailResponse(PostResponse):
    """Schema for post detail with comments and routing logs."""

    comments: List[CommentResponse] = []
    routing_logs: List[RoutingLogResponse] = []
