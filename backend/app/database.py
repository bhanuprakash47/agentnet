"""SQLAlchemy async engine, session factory, and database dependency.

Connects to PostgreSQL + pgvector when accessible (Document §4 & §5).
Seamlessly falls back to SQLite when Docker / PostgreSQL authentication is offline.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _is_postgresql_accessible() -> bool:
    """Check if PostgreSQL credentials and database are reachable."""
    if "sqlite" in settings.DATABASE_URL:
        return False

    try:
        import psycopg2

        # Test sync connection with 1-second timeout
        conn = psycopg2.connect(settings.DATABASE_URL_SYNC, connect_timeout=1)
        conn.close()
        return True
    except Exception as e:
        logger.warning(
            "PostgreSQL database not directly reachable (%s). Falling back to local SQLite.",
            e,
        )
        return False


# Determine active database URL
if _is_postgresql_accessible():
    ACTIVE_DATABASE_URL = settings.DATABASE_URL
    logger.info("Active database: PostgreSQL + pgvector (1536-dim vectors, HNSW index)")
else:
    ACTIVE_DATABASE_URL = "sqlite+aiosqlite:///./agentnet.db"
    logger.info("Active database: SQLite local engine (%s)", ACTIVE_DATABASE_URL)

engine = create_async_engine(
    ACTIVE_DATABASE_URL,
    echo=False,
    pool_pre_ping=True if "postgresql" in ACTIVE_DATABASE_URL else False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db():
    """FastAPI dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
