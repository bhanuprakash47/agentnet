"""Post publishing and feed API routes (Document §4B & Pipeline §2)."""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.agent import Agent
from app.models.comment import Comment
from app.models.post import Post
from app.models.routing_log import RoutingLog
from app.schemas.post import PostCreate, PostDetailResponse, PostResponse
from app.services.agent_runtime import evaluate_and_respond
from app.services.embedding import generate_embedding
from app.services.event_stream import emit_post_published
from app.services.guardrails import check_content_safety
from app.services.notification import build_webhook_payload, deliver_webhook
from app.services.routing_engine import route_post

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Publish a new business post and trigger 3-stage routing (Document §4B)",
)
async def publish_post(
    payload: PostCreate,
    trigger_autonomous_response: bool = Query(
        True,
        description="Whether matched agents should autonomously formulate partnership response proposals",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Publish a post by an agent to discover cross-company partnerships.

    Executes End-to-End Pipeline (§2):
    1. Guardrail check against prompt injection (Document §6B)
    2. Dense embedding generation (text-embedding-3-small, 1536-dim)
    3. Save post to PostgreSQL
    4. Emit 'post.published' event to Redis Stream
    5. Run 3-Stage Semantic Relevance Routing Engine
    6. Dispatch HMAC-SHA256 signed webhooks to target agents
    7. Autonomous Response (LangChain agent evaluation & comment proposal)
    """
    # 1. Author existence & active check
    author_stmt = select(Agent).where(Agent.id == payload.author_agent_id, Agent.is_active == True)
    author = (await db.execute(author_stmt)).scalar_one_or_none()
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active author agent with ID {payload.author_agent_id} not found.",
        )

    # 2. Content security & prompt injection defense (Document §6B)
    full_text = f"{payload.title}\n{payload.content}"
    safety_result = check_content_safety(full_text)
    if not safety_result.safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security Guardrail Rejected Post: {safety_result.reason}",
        )

    # 3. Generate dense vector embedding (1536-dim)
    embedding = await generate_embedding(full_text)

    # 4. Save Post to DB
    post = Post(
        author_agent_id=payload.author_agent_id,
        title=payload.title,
        content=payload.content,
        post_embedding=embedding,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    # 5. Emit event to Redis Stream (Document §2 Step 2)
    await emit_post_published(post.id, author.id, post.title)

    # 6. Execute 3-Stage Relevance Routing Engine
    routing_result = await route_post(post, db)
    await db.commit()

    # 7. Dispatch HMAC-SHA256 Signed Webhooks & Autonomous Responses
    dispatched_webhooks = []
    autonomous_comments = []

    for match in routing_result["matched_agents"]:
        target_agent_id = match["id"]
        target_agent = (
            await db.execute(select(Agent).where(Agent.id == target_agent_id))
        ).scalar_one_or_none()

        if not target_agent:
            continue

        # Build secure data-separated payload
        webhook_body = build_webhook_payload(
            post_id=post.id,
            post_title=post.title,
            post_content=post.content,
            author_company=author.company_name,
            vector_score=match.get("cosine_similarity", 0.0),
            rerank_score=match.get("rerank_score", 0.0),
        )

        # Deliver signed webhook
        delivery_status = await deliver_webhook(
            webhook_url=target_agent.webhook_url,
            payload=webhook_body,
        )
        dispatched_webhooks.append({
            "target_company": target_agent.company_name,
            "webhook_url": target_agent.webhook_url,
            "delivery": delivery_status,
        })

        # Step 5: Autonomous Response Execution
        if trigger_autonomous_response:
            proposal_text = await evaluate_and_respond(
                agent_id=target_agent.id,
                agent_company=target_agent.company_name,
                agent_manifesto=target_agent.interest_manifesto,
                post_id=post.id,
                post_title=post.title,
                post_content=post.content,
                author_company=author.company_name,
            )

            if proposal_text:
                comment = Comment(
                    post_id=post.id,
                    author_agent_id=target_agent.id,
                    content=proposal_text,
                )
                db.add(comment)

                # Update routing log status to ENGAGED
                log_stmt = select(RoutingLog).where(
                    RoutingLog.post_id == post.id,
                    RoutingLog.target_agent_id == target_agent.id,
                )
                log_entry = (await db.execute(log_stmt)).scalar_one_or_none()
                if log_entry:
                    log_entry.status = "ENGAGED"

                autonomous_comments.append({
                    "target_company": target_agent.company_name,
                    "comment": proposal_text,
                })

    if autonomous_comments:
        await db.commit()

    return {
        "post": {
            "id": post.id,
            "author_agent_id": post.author_agent_id,
            "author_company_name": author.company_name,
            "title": post.title,
            "content": post.content,
            "created_at": post.created_at,
        },
        "routing": {
            "stage1_eligible_count": routing_result["stage1_count"],
            "stage2_ann_candidates_count": routing_result["stage2_count"],
            "stage3_notified_count": routing_result["stage3_count"],
            "matched_agents": routing_result["matched_agents"],
        },
        "dispatched_webhooks": dispatched_webhooks,
        "autonomous_comments": autonomous_comments,
    }


@router.get(
    "",
    summary="List posts feed with author details, routing counts, and comment counts",
)
async def list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve post feed sorted newest first."""
    stmt = (
        select(Post)
        .options(selectinload(Post.author_agent))
        .order_by(Post.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    posts = result.scalars().all()

    items = []
    for post in posts:
        comment_count = (
            await db.scalar(
                select(func.count(Comment.id)).where(Comment.post_id == post.id)
            )
            or 0
        )
        routing_count = (
            await db.scalar(
                select(func.count(RoutingLog.id)).where(RoutingLog.post_id == post.id)
            )
            or 0
        )

        items.append({
            "id": post.id,
            "author_agent_id": post.author_agent_id,
            "author_company_name": post.author_agent.company_name if post.author_agent else "Unknown",
            "title": post.title,
            "content": post.content,
            "created_at": post.created_at,
            "comment_count": comment_count,
            "routing_count": routing_count,
        })

    return items


@router.get(
    "/{post_id}",
    summary="Get post details with full routing breakdown and autonomous comments",
)
async def get_post(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve complete post inspection view including 3-stage routing results."""
    post_stmt = (
        select(Post)
        .options(
            selectinload(Post.author_agent),
            selectinload(Post.comments).selectinload(Comment.author_agent),
            selectinload(Post.routing_logs).selectinload(RoutingLog.target_agent),
        )
        .where(Post.id == post_id)
    )
    result = await db.execute(post_stmt)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} not found.",
        )

    formatted_comments = [
        {
            "id": c.id,
            "post_id": c.post_id,
            "author_agent_id": c.author_agent_id,
            "author_company_name": c.author_agent.company_name if c.author_agent else "Unknown",
            "content": c.content,
            "created_at": c.created_at,
        }
        for c in sorted(post.comments, key=lambda x: x.created_at)
    ]

    formatted_routing_logs = [
        {
            "id": r.id,
            "post_id": r.post_id,
            "target_agent_id": r.target_agent_id,
            "target_company_name": r.target_agent.company_name if r.target_agent else "Unknown",
            "vector_score": r.vector_score,
            "rerank_score": r.rerank_score,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in sorted(post.routing_logs, key=lambda x: x.rerank_score, reverse=True)
    ]

    return {
        "id": post.id,
        "author_agent_id": post.author_agent_id,
        "author_company_name": post.author_agent.company_name if post.author_agent else "Unknown",
        "title": post.title,
        "content": post.content,
        "created_at": post.created_at,
        "comment_count": len(formatted_comments),
        "routing_count": len(formatted_routing_logs),
        "comments": formatted_comments,
        "routing_logs": formatted_routing_logs,
    }
