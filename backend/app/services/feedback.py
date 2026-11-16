"""Closed-Loop Feedback & Dynamic Profile Learning Service (Document §6A).

Implements:
1. Engagement Rate Calculation: R = Comments Received / Notifications Sent
2. Dynamic Profile Learning: If an agent consistently ignores notifications
   related to a topic over N instances, updates the agent's dynamic preference
   vector by applying a negative gradient shift away from unengaged post embeddings.
"""

import logging
from typing import Dict, List, Optional
from uuid import UUID

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.comment import Comment
from app.models.post import Post
from app.models.routing_log import RoutingLog

logger = logging.getLogger(__name__)


async def compute_engagement_rate(
    agent_id: UUID,
    db: AsyncSession,
) -> Dict[str, float]:
    """
    Calculate the engagement rate R for an agent.

    R = Comments Made / Notifications Received
    Also calculates:
      - notifications_count
      - engaged_count
      - comments_authored_count
    """
    # Total notifications sent to this agent
    notif_stmt = select(func.count(RoutingLog.id)).where(
        RoutingLog.target_agent_id == agent_id
    )
    notif_res = await db.execute(notif_stmt)
    notifications_sent = notif_res.scalar() or 0

    # Total engaged notifications (status == 'ENGAGED')
    engaged_stmt = select(func.count(RoutingLog.id)).where(
        RoutingLog.target_agent_id == agent_id,
        RoutingLog.status == "ENGAGED",
    )
    engaged_res = await db.execute(engaged_stmt)
    engaged_count = engaged_res.scalar() or 0

    # Total comments written by this agent
    comments_stmt = select(func.count(Comment.id)).where(
        Comment.author_agent_id == agent_id
    )
    comments_res = await db.execute(comments_stmt)
    comments_authored = comments_res.scalar() or 0

    engagement_rate = (
        (engaged_count / notifications_sent) if notifications_sent > 0 else 0.0
    )

    return {
        "notifications_sent": notifications_sent,
        "engaged_count": engaged_count,
        "comments_authored": comments_authored,
        "engagement_rate": round(engagement_rate, 4),
    }


async def update_agent_profile_vector(
    agent_id: UUID,
    db: AsyncSession,
    learning_rate: float = 0.05,
    ignore_threshold: int = 3,
) -> Optional[Dict[str, float]]:
    """
    Apply negative gradient shift to the agent's interest embedding.

    Per Document §6A:
    'If an agent consistently ignores notifications related to a topic over N instances,
    update the agent's dynamic preference vector by applying a negative gradient shift
    away from those unengaged post embeddings.'

    v_new = normalize(v_current - learning_rate * mean(ignored_embeddings))
    """
    # 1. Fetch unengaged (IGNORED or stale NOTIFIED) logs with post embeddings
    stmt = (
        select(Post.post_embedding)
        .join(RoutingLog, RoutingLog.post_id == Post.id)
        .where(
            RoutingLog.target_agent_id == agent_id,
            RoutingLog.status.in_(["IGNORED", "NOTIFIED"]),
            Post.post_embedding.isnot(None),
        )
        .order_by(RoutingLog.created_at.desc())
        .limit(ignore_threshold)
    )
    result = await db.execute(stmt)
    ignored_embeddings = [list(row[0]) for row in result.fetchall() if row[0] is not None]

    if len(ignored_embeddings) < ignore_threshold:
        logger.info(
            "Agent %s has %d ignored posts (threshold=%d). Skipping gradient update.",
            agent_id,
            len(ignored_embeddings),
            ignore_threshold,
        )
        return None

    # 2. Fetch current agent
    agent_stmt = select(Agent).where(Agent.id == agent_id)
    agent_res = await db.execute(agent_stmt)
    agent = agent_res.scalar_one_or_none()
    if not agent or agent.interest_embedding is None:
        return None

    current_vec = np.array(list(agent.interest_embedding), dtype=np.float32)

    # 3. Compute mean of ignored post embeddings (negative gradient direction)
    ignored_matrix = np.array(ignored_embeddings, dtype=np.float32)
    mean_ignored_vec = np.mean(ignored_matrix, axis=0)

    # 4. Apply negative gradient shift: move away from unengaged content
    updated_vec = current_vec - (learning_rate * mean_ignored_vec)

    # 5. Re-normalize to unit hypersphere
    norm = np.linalg.norm(updated_vec)
    if norm > 0:
        updated_vec = updated_vec / norm

    # 6. Save back to database
    agent.interest_embedding = updated_vec.tolist()
    await db.flush()

    logger.info(
        "Applied negative gradient shift to agent %s: %d ignored samples, lr=%.3f",
        agent.company_name,
        len(ignored_embeddings),
        learning_rate,
    )

    return {
        "shift_magnitude": float(np.linalg.norm(current_vec - updated_vec)),
        "samples_used": len(ignored_embeddings),
    }
