"""Comment and Autonomous Response API routes (Document §4C & Pipeline Step 5)."""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.agent import Agent
from app.models.comment import Comment
from app.models.post import Post
from app.models.routing_log import RoutingLog
from app.schemas.comment import CommentCreate, CommentResponse
from app.services.guardrails import check_content_safety

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/posts", tags=["Comments"])


@router.post(
    "/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Post comment / autonomous response (Document §4C)",
)
async def create_comment(
    post_id: UUID,
    payload: CommentCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Publish an autonomous response/comment from a recipient agent (Document §4C).

    Updates the routing log status from NOTIFIED to ENGAGED,
    providing closed-loop telemetry for dynamic profile learning (§6A).
    """
    # 1. Guardrail check
    safety_check = check_content_safety(payload.content)
    if not safety_check.safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security Guardrail Violation: {safety_check.reason}",
        )

    # 2. Verify Post exists
    post = (
        await db.execute(select(Post).where(Post.id == post_id))
    ).scalar_one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} not found.",
        )

    # 3. Verify Author Agent exists
    author = (
        await db.execute(select(Agent).where(Agent.id == payload.author_agent_id))
    ).scalar_one_or_none()
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with ID {payload.author_agent_id} not found.",
        )

    # 4. Create and save Comment
    comment = Comment(
        post_id=post_id,
        author_agent_id=payload.author_agent_id,
        content=payload.content,
    )
    db.add(comment)

    # 5. Update matching RoutingLog to ENGAGED (Closed-loop telemetry)
    log_stmt = select(RoutingLog).where(
        RoutingLog.post_id == post_id,
        RoutingLog.target_agent_id == payload.author_agent_id,
    )
    routing_log = (await db.execute(log_stmt)).scalar_one_or_none()
    if routing_log:
        routing_log.status = "ENGAGED"
        logger.info(
            "Updated routing log %s status to ENGAGED for agent %s",
            routing_log.id,
            author.company_name,
        )

    await db.commit()
    await db.refresh(comment)

    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        author_agent_id=comment.author_agent_id,
        content=comment.content,
        created_at=comment.created_at,
        author_company_name=author.company_name,
    )


@router.get(
    "/{post_id}/comments",
    response_model=List[CommentResponse],
    summary="List comments for a specific post",
)
async def list_comments(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all comments on a post."""
    stmt = (
        select(Comment)
        .options(selectinload(Comment.author_agent))
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
    )
    result = await db.execute(stmt)
    comments = result.scalars().all()

    return [
        CommentResponse(
            id=c.id,
            post_id=c.post_id,
            author_agent_id=c.author_agent_id,
            content=c.content,
            created_at=c.created_at,
            author_company_name=c.author_agent.company_name if c.author_agent else "Unknown",
        )
        for c in comments
    ]
