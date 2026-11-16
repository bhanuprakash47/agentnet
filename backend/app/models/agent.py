"""Agent database model (Document §4.1)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, String, Text, Uuid
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import UniversalVector


class Agent(Base):
    """Represents an AI agent registered on the AgentNet platform."""

    __tablename__ = "agents"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(255), nullable=False)
    industry_category = Column(String(100), nullable=False)
    webhook_url = Column(Text, nullable=False)
    interest_manifesto = Column(Text, nullable=False)
    interest_embedding = Column(UniversalVector(1536))
    trust_score = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    posts = relationship("Post", back_populates="author_agent", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author_agent", cascade="all, delete-orphan")
    routing_logs = relationship("RoutingLog", back_populates="target_agent", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, company_name='{self.company_name}')>"
