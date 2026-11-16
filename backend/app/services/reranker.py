"""Cohere-based reranking service for Stage 3 of the routing pipeline."""

import logging
from typing import Any, Dict, List

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def rerank_candidates(
    query: str,
    candidates: List[Dict[str, Any]],
    threshold: float,
) -> List[Dict[str, Any]]:
    """
    Rerank candidate agents using Cohere Rerank v3.

    Each candidate dict must have:
      - id: agent UUID
      - company_name: str
      - interest_manifesto: str
      - cosine_similarity: float (from Stage 2)

    Args:
        query: The post content used as the rerank query.
        candidates: List of candidate dicts from Stage 2.
        threshold: Minimum rerank relevance score to keep a candidate.

    Returns:
        Filtered and reranked list of candidate dicts with added 'rerank_score' field.
    """
    if not candidates:
        logger.info("No candidates to rerank.")
        return []

    if not settings.COHERE_API_KEY:
        logger.warning(
            "COHERE_API_KEY not set — falling back to vector cosine similarity scores "
            "as rerank scores. Set the key in .env for production reranking."
        )
        results = []
        for candidate in candidates:
            score = candidate.get("cosine_similarity", 0.0)
            candidate["rerank_score"] = score
            if score >= threshold:
                results.append(candidate)
        results.sort(key=lambda x: x["rerank_score"], reverse=True)
        logger.info(
            "Fallback rerank: %d/%d candidates passed threshold %.2f",
            len(results),
            len(candidates),
            threshold,
        )
        return results

    try:
        import cohere

        co = cohere.Client(api_key=settings.COHERE_API_KEY)
        documents = [c["interest_manifesto"] for c in candidates]

        response = co.rerank(
            model="rerank-english-v3.0",
            query=query,
            documents=documents,
            top_n=len(documents),
        )

        results = []
        for result in response.results:
            idx = result.index
            score = result.relevance_score
            candidate = candidates[idx].copy()
            candidate["rerank_score"] = score
            if score >= threshold:
                results.append(candidate)

        results.sort(key=lambda x: x["rerank_score"], reverse=True)
        logger.info(
            "Cohere rerank: %d/%d candidates passed threshold %.2f",
            len(results),
            len(candidates),
            threshold,
        )
        return results

    except Exception as e:
        logger.error("Cohere rerank failed: %s. Falling back to vector scores.", e)
        results = []
        for candidate in candidates:
            score = candidate.get("cosine_similarity", 0.0)
            candidate["rerank_score"] = score
            if score >= threshold:
                results.append(candidate)
        results.sort(key=lambda x: x["rerank_score"], reverse=True)
        return results
