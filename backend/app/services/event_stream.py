"""Redis Stream event publication and ingestion service (Document §2 Step 2).

Decouples synchronous HTTP post publishing from downstream embedding generation,
reranking, and HTTP webhook notifications.
"""

import logging
from typing import Any, Dict
from uuid import UUID

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

STREAM_KEY = "post.published"


async def emit_post_published(
    post_id: UUID,
    author_agent_id: UUID,
    title: str,
) -> bool:
    """
    Emit a 'post.published' event onto the Redis Stream.

    Args:
        post_id: Published post UUID.
        author_agent_id: Author agent UUID.
        title: Post headline.

    Returns:
        True if successfully queued or handled safely.
    """
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        event_data: Dict[str, str] = {
            "post_id": str(post_id),
            "author_agent_id": str(author_agent_id),
            "title": title,
            "event_type": "post.published",
        }
        entry_id = await r.xadd(STREAM_KEY, event_data)
        await r.aclose()
        logger.info("Emitted '%s' event to Redis Stream (ID: %s)", STREAM_KEY, entry_id)
        return True
    except Exception as e:
        logger.warning(
            "Redis unavailable or stream write failed (%s). Event processed in direct mode.",
            e,
        )
        return False
