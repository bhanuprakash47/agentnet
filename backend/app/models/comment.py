"""Comment database model (Document §4.4)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Text, Uuid
from sqlalchemy.orm import relationship

from app.database import Base


class Comment(Base):
    """Represents an autonomous partnership response / comment."""

    __tablename__ = "comments"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    author_agent_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    post = relationship("Post", back_populates="comments")
    author_agent = relationship("Agent", back_populates="comments")

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, author='{self.author_agent_id}')>"
