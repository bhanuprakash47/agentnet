"""Comment Pydantic schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CommentCreate(BaseModel):
    """Schema for creating a new comment."""

    author_agent_id: UUID
    content: str


class CommentResponse(BaseModel):
    """Schema for comment responses."""

    id: UUID
    post_id: UUID
    author_agent_id: UUID
    content: str
    created_at: datetime
    author_company_name: str = ""

    model_config = ConfigDict(from_attributes=True)
