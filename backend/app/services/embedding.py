"""Embedding generation service using OpenAI text-embedding-3-small."""

import logging
import random
from typing import List

import openai

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_client = None


def _get_client() -> openai.AsyncOpenAI:
    """Lazily create and return the AsyncOpenAI client."""
    global _client
    if _client is None:
        _client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def generate_embedding(text: str) -> List[float]:
    """
    Generate a 1536-dimensional embedding vector for the given text.

    Uses OpenAI text-embedding-3-small when API key is available.
    Falls back to a random normalized vector for development/testing.

    Args:
        text: The input text to embed.

    Returns:
        A list of 1536 floats representing the embedding vector.
    """
    if not settings.OPENAI_API_KEY:
        logger.warning(
            "OPENAI_API_KEY not set — returning random embedding vector. "
            "Set the key in .env for production use."
        )
        vector = [random.gauss(0, 1) for _ in range(settings.VECTOR_DIMENSION)]
        magnitude = sum(x * x for x in vector) ** 0.5
        return [x / magnitude for x in vector]

    try:
        client = _get_client()
        response = await client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text,
        )
        embedding = response.data[0].embedding
        logger.info("Generated embedding for text (length=%d chars)", len(text))
        return embedding
    except openai.APIError as e:
        logger.error("OpenAI API error generating embedding: %s", e)
        raise
    except Exception as e:
        logger.error("Unexpected error generating embedding: %s", e)
        raise
