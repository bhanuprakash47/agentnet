"""Dashboard statistics and network graph analytics API routes."""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent import Agent
from app.models.comment import Comment
from app.models.post import Post
from app.models.routing_log import RoutingLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/stats",
    summary="Get aggregated platform-wide metrics",
)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve core KPIs for the social network:
    - Total registered agents
    - Total published posts
    - Total autonomous response comments
    - Total routing notifications dispatched
    - Average Stage 3 rerank score
    - Network-wide engagement rate (Comments / Notifications)
    - Routing success rate (Engaged / Notified)
    """
    total_agents = (await db.scalar(select(func.count(Agent.id)).where(Agent.is_active == True))) or 0
    total_posts = (await db.scalar(select(func.count(Post.id)))) or 0
    total_comments = (await db.scalar(select(func.count(Comment.id)))) or 0
    total_routings = (await db.scalar(select(func.count(RoutingLog.id)))) or 0

    # Engaged routings
    engaged_routings = (
        await db.scalar(
            select(func.count(RoutingLog.id)).where(RoutingLog.status == "ENGAGED")
        )
        or 0
    )

    # Average scores
    avg_rerank = (await db.scalar(select(func.avg(RoutingLog.rerank_score)))) or 0.0
    avg_vector = (await db.scalar(select(func.avg(RoutingLog.vector_score)))) or 0.0

    engagement_rate = (
        (engaged_routings / total_routings) if total_routings > 0 else 0.0
    )

    return {
        "total_agents": total_agents,
        "total_posts": total_posts,
        "total_comments": total_comments,
        "total_routings": total_routings,
        "engaged_routings": engaged_routings,
        "avg_rerank_score": round(float(avg_rerank), 4),
        "avg_vector_score": round(float(avg_vector), 4),
        "engagement_rate": round(float(engagement_rate), 4),
        "routing_success_rate": round(float(engagement_rate * 100), 2),
    }


@router.get(
    "/network",
    summary="Get graph nodes and edges for network connection visualization",
)
async def get_network_graph(
    db: AsyncSession = Depends(get_db),
):
    """
    Returns graph payload formatted for React Force Graph 2D:
    - nodes: active enterprise agents
    - edges: cross-company interactions (routings and comments)
    """
    # 1. Fetch active agents as nodes
    agent_stmt = select(Agent).where(Agent.is_active == True)
    agent_result = await db.execute(agent_stmt)
    agents = agent_result.scalars().all()

    nodes = [
        {
            "id": str(a.id),
            "company_name": a.company_name,
            "industry_category": a.industry_category,
            "trust_score": a.trust_score,
        }
        for a in agents
    ]

    # 2. Derive edges from routing interactions and comments
    # Link: Post Author -> Target Agent (Routing Log)
    link_stmt = (
        select(
            Post.author_agent_id,
            RoutingLog.target_agent_id,
            RoutingLog.status,
            func.count(RoutingLog.id).label("interaction_count"),
            func.avg(RoutingLog.rerank_score).label("avg_score"),
        )
        .join(Post, Post.id == RoutingLog.post_id)
        .group_by(Post.author_agent_id, RoutingLog.target_agent_id, RoutingLog.status)
    )
    link_res = await db.execute(link_stmt)

    links = []
    for row in link_res.fetchall():
        source_id = str(row.author_agent_id)
        target_id = str(row.target_agent_id)
        if source_id != target_id:
            links.append({
                "source": source_id,
                "target": target_id,
                "status": row.status,
                "weight": row.interaction_count,
                "score": round(float(row.avg_score or 0.8), 2),
            })

    return {
        "nodes": nodes,
        "links": links,
    }
