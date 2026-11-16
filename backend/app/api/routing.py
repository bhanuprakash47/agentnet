"""Routing log analytics and inspection API routes."""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.routing_log import RoutingLog
from app.schemas.routing_log import RoutingLogResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routing", tags=["Routing"])


@router.get(
    "/logs",
    response_model=List[RoutingLogResponse],
    summary="List routing logs with optional filters",
)
async def list_routing_logs(
    post_id: Optional[UUID] = Query(None, description="Filter by post ID"),
    target_agent_id: Optional[UUID] = Query(None, description="Filter by target agent ID"),
    status: Optional[str] = Query(None, description="Filter by status (NOTIFIED, ENGAGED, IGNORED, FAILED)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve historical routing logs with target agent company names."""
    query = select(RoutingLog).options(selectinload(RoutingLog.target_agent))

    if post_id:
        query = query.where(RoutingLog.post_id == post_id)
    if target_agent_id:
        query = query.where(RoutingLog.target_agent_id == target_agent_id)
    if status:
        query = query.where(RoutingLog.status == status.upper())

    query = query.order_by(RoutingLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        RoutingLogResponse(
            id=log.id,
            post_id=log.post_id,
            target_agent_id=log.target_agent_id,
            vector_score=round(log.vector_score, 4),
            rerank_score=round(log.rerank_score, 4),
            status=log.status,
            created_at=log.created_at,
            target_company_name=log.target_agent.company_name if log.target_agent else "Unknown",
        )
        for log in logs
    ]


@router.get(
    "/logs/{post_id}",
    summary="Get 3-stage routing metrics and logs for a specific post",
)
async def get_post_routing_breakdown(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Detailed stage metrics and matched candidates for a single post."""
    stmt = (
        select(RoutingLog)
        .options(selectinload(RoutingLog.target_agent))
        .where(RoutingLog.post_id == post_id)
        .order_by(RoutingLog.rerank_score.desc())
    )
    result = await db.execute(stmt)
    logs = result.scalars().all()

    notified = [l for l in logs if l.status == "NOTIFIED"]
    engaged = [l for l in logs if l.status == "ENGAGED"]
    ignored = [l for l in logs if l.status == "IGNORED"]

    return {
        "post_id": post_id,
        "total_notified": len(logs),
        "status_summary": {
            "notified": len(notified),
            "engaged": len(engaged),
            "ignored": len(ignored),
        },
        "logs": [
            {
                "id": l.id,
                "target_agent_id": l.target_agent_id,
                "target_company_name": l.target_agent.company_name if l.target_agent else "Unknown",
                "vector_score": round(l.vector_score, 4),
                "rerank_score": round(l.rerank_score, 4),
                "status": l.status,
                "created_at": l.created_at,
            }
            for l in logs
        ],
    }
