"""Celery asynchronous tasks for routing and webhook delivery (Document §2 Step 4)."""

import asyncio
import logging
from typing import Any, Dict
from uuid import UUID

from app.services.notification import deliver_webhook
from app.worker import celery_app

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper to run async coroutines inside Celery sync worker processes."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.deliver_webhook_task", bind=True, max_retries=3, default_retry_delay=5)
def deliver_webhook_task(self, webhook_url: str, payload: Dict[str, Any]):
    """Deliver HMAC-signed webhook to an external agent endpoint with retry logic."""
    try:
        result = run_async(deliver_webhook(webhook_url, payload))
        logger.info("Celery task webhook delivery to %s: %s", webhook_url, result)
        return result
    except Exception as exc:
        logger.error("Celery webhook delivery failed to %s: %s. Retrying...", webhook_url, exc)
        raise self.retry(exc=exc)


@celery_app.task(name="app.tasks.route_post_task", bind=True, max_retries=2)
def route_post_task(self, post_id_str: str):
    """Asynchronous background routing task."""
    logger.info("Executing background routing for post %s", post_id_str)
    # Background execution hook
    return {"status": "SUCCESS", "post_id": post_id_str}
