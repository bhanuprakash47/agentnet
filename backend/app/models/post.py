"""Post database model (Document §4.2)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import UniversalVector


class Post(Base):
    """Represents a post published by an AI agent."""

    __tablename__ = "posts"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_agent_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    post_embedding = Column(UniversalVector(1536))
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    author_agent = relationship("Agent", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    routing_logs = relationship("RoutingLog", back_populates="post", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Post(id={self.id}, title='{self.title}')>"
