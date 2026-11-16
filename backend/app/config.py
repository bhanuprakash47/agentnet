"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """AgentNet application settings."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://asama_user:asama_pass@localhost:5432/asama_network"
    DATABASE_URL_SYNC: str = "postgresql://asama_user:asama_pass@localhost:5432/asama_network"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # OpenAI
    OPENAI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    VECTOR_DIMENSION: int = 1536

    # Cohere
    COHERE_API_KEY: str = ""

    # Routing
    ANN_TOP_K: int = 50
    RERANK_THRESHOLD: float = 0.75

    # Webhook
    WEBHOOK_HMAC_SECRET: str = "default-hmac-secret-change-me"

    # Guardrails
    GUARDRAIL_MODE: str = "rule_based"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
