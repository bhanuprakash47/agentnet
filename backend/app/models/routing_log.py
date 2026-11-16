"""RoutingLog database model (Document §4.3)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Uuid
from sqlalchemy.orm import relationship

from app.database import Base


class RoutingLog(Base):
    """Tracks how posts are routed to target agents via the 3-stage pipeline."""

    __tablename__ = "routing_logs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_agent_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    vector_score = Column(Float, nullable=False)
    rerank_score = Column(Float, nullable=False)
    status = Column(String(50), default="NOTIFIED")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    post = relationship("Post", back_populates="routing_logs")
    target_agent = relationship("Agent", back_populates="routing_logs")

    def __repr__(self) -> str:
        return f"<RoutingLog(id={self.id}, status='{self.status}')>"
