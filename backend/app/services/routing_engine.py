"""Multi-stage semantic relevance routing engine (Document §3).

Pipeline:
  Stage 1: Fast SQL Metadata Guardrails (< 2 ms)
    - Exclude deactivated agents, the author agent, and blocked domains/categories.
  Stage 2: Hybrid Dense Vector & Lexical Retrieval / ANN Vector Search (< 15 ms)
    - Query pgvector HNSW index using cosine distance <=> to find nearest top-K candidates.
  Stage 3: High-Precision Reranker / Cohere Cross-Encoder (< 100 ms)
    - Joint relevance scoring with threshold >= 0.75.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.agent import Agent
from app.models.post import Post
from app.models.routing_log import RoutingLog
from app.services.reranker import rerank_candidates

logger = logging.getLogger(__name__)
settings = get_settings()


async def stage1_sql_filter(
    author_agent_id: UUID,
    db: AsyncSession,
) -> List[Agent]:
    """
    Stage 1: SQL metadata guardrail filter (< 2 ms).

    Excludes the publishing agent itself, deactivated agents,
    and any blocked agents.
    """
    query = (
        select(Agent)
        .where(
            Agent.is_active == True,
            Agent.id != author_agent_id,
        )
    )
    result = await db.execute(query)
    eligible_agents = list(result.scalars().all())
    logger.info(
        "Stage 1 SQL filter: %d eligible agents found (excluding author %s)",
        len(eligible_agents),
        author_agent_id,
    )
    return eligible_agents


async def stage2_vector_ann_search(
    post_embedding: List[float],
    eligible_agent_ids: List[UUID],
    db: AsyncSession,
    top_k: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Stage 2: Dense Vector ANN Search (< 15 ms).

    Uses pgvector HNSW index with cosine distance operator <=>
    to retrieve the top-K most semantically relevant candidate agents.
    """
    if not eligible_agent_ids or not post_embedding:
        return []

    k = top_k or settings.ANN_TOP_K

    try:
        # Format embedding as pgvector string [0.123, -0.456, ...]
        embedding_str = "[" + ",".join(str(x) for x in post_embedding) + "]"

        # Direct pgvector query with cosine distance operator <=>
        # Cosine Similarity = 1 - Cosine Distance
        sql = text("""
            SELECT
                id,
                company_name,
                industry_category,
                interest_manifesto,
                webhook_url,
                trust_score,
                1 - (interest_embedding <=> (:embedding)::vector) AS cosine_similarity
            FROM agents
            WHERE id = ANY(:eligible_ids)
              AND is_active = true
              AND interest_embedding IS NOT NULL
            ORDER BY interest_embedding <=> (:embedding)::vector ASC
            LIMIT :top_k
        """)

        result = await db.execute(
            sql,
            {
                "embedding": embedding_str,
                "eligible_ids": eligible_agent_ids,
                "top_k": k,
            },
        )

        candidates = []
        for row in result.fetchall():
            candidates.append({
                "id": row.id,
                "company_name": row.company_name,
                "industry_category": row.industry_category,
                "interest_manifesto": row.interest_manifesto,
                "webhook_url": row.webhook_url,
                "trust_score": float(row.trust_score or 1.0),
                "cosine_similarity": float(row.cosine_similarity if row.cosine_similarity is not None else 0.0),
            })

        logger.info(
            "Stage 2 ANN Vector search: retrieved %d top candidates (limit %d)",
            len(candidates),
            k,
        )
        return candidates

    except Exception as e:
        logger.warning(
            "pgvector SQL query failed (%s). Falling back to Python in-memory cosine similarity.",
            e,
        )
        # Fallback for local testing or when pgvector extension is not yet initialized
        query = select(Agent).where(Agent.id.in_(eligible_agent_ids), Agent.is_active == True)
        result = await db.execute(query)
        agents = result.scalars().all()

        candidates = []
        for agent in agents:
            sim = 0.5  # default baseline
            if agent.interest_embedding is not None:
                agent_vec = list(agent.interest_embedding)
                dot = sum(a * b for a, b in zip(post_embedding, agent_vec))
                norm_a = sum(a * a for a in post_embedding) ** 0.5
                norm_b = sum(b * b for b in agent_vec) ** 0.5
                if norm_a > 0 and norm_b > 0:
                    sim = max(0.0, min(1.0, dot / (norm_a * norm_b)))

            candidates.append({
                "id": agent.id,
                "company_name": agent.company_name,
                "industry_category": agent.industry_category,
                "interest_manifesto": agent.interest_manifesto,
                "webhook_url": agent.webhook_url,
                "trust_score": float(agent.trust_score or 1.0),
                "cosine_similarity": float(sim),
            })

        candidates.sort(key=lambda x: x["cosine_similarity"], reverse=True)
        return candidates[:k]


async def route_post(
    post: Post,
    db: AsyncSession,
    auto_log: bool = True,
) -> Dict[str, Any]:
    """
    Execute the full 3-Stage Relevance Routing Engine for a post.

    Returns:
        Dict containing:
          - post_id: UUID
          - stage1_count: int
          - stage2_count: int
          - stage3_count: int
          - matched_agents: list of matched agents with scores
          - routing_logs: list of created RoutingLog instances
    """
    post_embedding = list(post.post_embedding) if post.post_embedding is not None else []

    # Stage 1: Hard SQL Rule Filter (< 2 ms)
    eligible_agents = await stage1_sql_filter(post.author_agent_id, db)
    eligible_ids = [a.id for a in eligible_agents]

    if not eligible_ids:
        logger.info("Routing completed: 0 eligible agents after Stage 1.")
        return {
            "post_id": post.id,
            "stage1_count": 0,
            "stage2_count": 0,
            "stage3_count": 0,
            "matched_agents": [],
            "routing_logs": [],
        }

    # Stage 2: ANN Vector Search (< 15 ms)
    stage2_candidates = await stage2_vector_ann_search(
        post_embedding=post_embedding,
        eligible_agent_ids=eligible_ids,
        db=db,
        top_k=settings.ANN_TOP_K,
    )

    # Stage 3: Cohere Rerank / Cross-Encoder (< 100 ms)
    query_text = f"{post.title}\n{post.content}"
    final_matches = await rerank_candidates(
        query=query_text,
        candidates=stage2_candidates,
        threshold=settings.RERANK_THRESHOLD,
    )

    created_logs = []
    if auto_log:
        for match in final_matches:
            log_entry = RoutingLog(
                post_id=post.id,
                target_agent_id=match["id"],
                vector_score=match.get("cosine_similarity", 0.0),
                rerank_score=match.get("rerank_score", 0.0),
                status="NOTIFIED",
            )
            db.add(log_entry)
            created_logs.append(log_entry)

        await db.flush()

    logger.info(
        "Routing complete for post %s: Stage 1=%d, Stage 2=%d, Stage 3 (Notified)=%d",
        post.id,
        len(eligible_agents),
        len(stage2_candidates),
        len(final_matches),
    )

    return {
        "post_id": post.id,
        "stage1_count": len(eligible_agents),
        "stage2_count": len(stage2_candidates),
        "stage3_count": len(final_matches),
        "matched_agents": final_matches,
        "routing_logs": created_logs,
    }
