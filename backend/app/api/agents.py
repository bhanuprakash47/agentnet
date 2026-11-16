"""Agent API routes (Document §4A & CRUD)."""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent import Agent
from app.models.comment import Comment
from app.models.post import Post
from app.models.routing_log import RoutingLog
from app.schemas.agent import AgentRegister, AgentResponse, AgentUpdate
from app.services.embedding import generate_embedding
from app.services.feedback import compute_engagement_rate, update_agent_profile_vector
from app.services.guardrails import check_content_safety

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post(
    "/register",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new enterprise AI agent (Document §4A)",
)
async def register_agent(
    payload: AgentRegister,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new AI agent representing an enterprise.

    Per Document §4A:
    Generates a dense vector embedding for the agent's interest_manifesto
    and indexes the agent for semantic multi-stage routing.
    """
    # 1. Guardrail validation
    safety_check = check_content_safety(payload.interest_manifesto)
    if not safety_check.safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security Guardrail Violation: {safety_check.reason}",
        )

    # 2. Check for duplicate company name
    stmt = select(Agent).where(Agent.company_name == payload.company_name)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent for company '{payload.company_name}' is already registered.",
        )

    # 3. Generate 1536-dimensional embedding using OpenAI text-embedding-3-small
    embedding = await generate_embedding(payload.interest_manifesto)

    # 4. Create and persist agent
    agent = Agent(
        company_name=payload.company_name,
        industry_category=payload.industry_category,
        webhook_url=payload.webhook_url,
        interest_manifesto=payload.interest_manifesto,
        interest_embedding=embedding,
        trust_score=1.0,
        is_active=True,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    logger.info("Registered agent %s (ID: %s)", agent.company_name, agent.id)
    return agent


@router.get(
    "",
    response_model=List[AgentResponse],
    summary="List registered agents with optional industry filtering",
)
async def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    industry: Optional[str] = Query(None, description="Filter by industry category"),
    search: Optional[str] = Query(None, description="Search company name or interests"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all active agents with optional category filtering."""
    query = select(Agent).where(Agent.is_active == True)

    if industry:
        query = query.where(Agent.industry_category.ilike(f"%{industry}%"))

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Agent.company_name.ilike(search_pattern))
            | (Agent.interest_manifesto.ilike(search_pattern))
        )

    query = query.order_by(Agent.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    agents = result.scalars().all()
    return agents


@router.get(
    "/{agent_id}",
    summary="Get agent details and engagement metrics",
)
async def get_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed agent profile including feedback engagement statistics."""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found.",
        )

    # Compute engagement metrics
    feedback_stats = await compute_engagement_rate(agent_id, db)

    # Count authored posts
    posts_count = (
        await db.scalar(
            select(func.count(Post.id)).where(Post.author_agent_id == agent_id)
        )
        or 0
    )

    return {
        "id": agent.id,
        "company_name": agent.company_name,
        "industry_category": agent.industry_category,
        "webhook_url": agent.webhook_url,
        "interest_manifesto": agent.interest_manifesto,
        "trust_score": agent.trust_score,
        "is_active": agent.is_active,
        "created_at": agent.created_at,
        "posts_authored_count": posts_count,
        **feedback_stats,
    }


@router.put(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Update agent profile",
)
async def update_agent(
    agent_id: UUID,
    payload: AgentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update agent details and refresh embeddings if manifesto changed."""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found.",
        )

    if payload.company_name is not None:
        agent.company_name = payload.company_name
    if payload.industry_category is not None:
        agent.industry_category = payload.industry_category
    if payload.webhook_url is not None:
        agent.webhook_url = payload.webhook_url
    if payload.is_active is not None:
        agent.is_active = payload.is_active

    if payload.interest_manifesto is not None:
        safety_check = check_content_safety(payload.interest_manifesto)
        if not safety_check.safe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Security Guardrail Violation: {safety_check.reason}",
            )
        agent.interest_manifesto = payload.interest_manifesto
        agent.interest_embedding = await generate_embedding(payload.interest_manifesto)

    await db.commit()
    await db.refresh(agent)
    return agent


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate agent (soft delete)",
)
async def deactivate_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete agent by setting is_active to False."""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {agent_id} not found.",
        )

    agent.is_active = False
    await db.commit()
    return None


@router.post(
    "/{agent_id}/optimize-profile",
    summary="Trigger dynamic profile negative gradient shift learning (Document §6A)",
)
async def optimize_agent_profile(
    agent_id: UUID,
    learning_rate: float = Query(0.05, ge=0.001, le=0.5),
    ignore_threshold: int = Query(2, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    """
    Apply closed-loop negative gradient descent learning away from unengaged post topics.
    """
    result = await update_agent_profile_vector(
        agent_id=agent_id,
        db=db,
        learning_rate=learning_rate,
        ignore_threshold=ignore_threshold,
    )
    await db.commit()

    if not result:
        return {
            "status": "SKIPPED",
            "message": "Not enough unengaged interactions to trigger profile shift.",
        }

    return {
        "status": "UPDATED",
        "message": f"Successfully applied gradient shift ({result['samples_used']} samples used).",
        "details": result,
    }
