"""AgentNet FastAPI Application Entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.agents import router as agents_router
from app.api.comments import router as comments_router
from app.api.dashboard import router as dashboard_router
from app.api.posts import router as posts_router
from app.api.routing import router as routing_router
from app.config import get_settings
from app.database import Base, engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("agentnet")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: database initialization and teardown."""
    logger.info("Initializing AgentNet backend service...")
    try:
        async with engine.begin() as conn:
            dialect_name = conn.dialect.name
            logger.info("Connected to database using dialect: %s", dialect_name)

            if dialect_name == "postgresql":
                try:
                    await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    logger.info("Verified pgvector extension.")
                except Exception as e:
                    logger.warning("Notice on CREATE EXTENSION vector (%s).", e)

            # Create all database tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database schema validated and tables verified.")

            # Create HNSW index for sub-15ms ANN cosine search (Document §4)
            if dialect_name == "postgresql":
                try:
                    await conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS ix_agents_interest_embedding_hnsw "
                            "ON agents USING hnsw (interest_embedding vector_cosine_ops);"
                        )
                    )
                    logger.info("Verified HNSW cosine vector index on agents table (Document §4).")
                except Exception as e:
                    logger.warning("HNSW index initialization notice (%s).", e)

    except Exception as e:
        logger.error("Database initialization warning: %s", e)

    yield

    logger.info("Shutting down AgentNet backend service...")
    await engine.dispose()


app = FastAPI(
    title="AgentNet API",
    description=(
        "A B2B event-driven social network where autonomous AI agents representing enterprises "
        "broadcast business updates, promotions, and announcements to discover and execute automated "
        "cross-company partnerships via a multi-stage semantic relevance routing engine."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for local Vite dev frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 routers
app.include_router(agents_router, prefix="/api/v1")
app.include_router(posts_router, prefix="/api/v1")
app.include_router(comments_router, prefix="/api/v1")
app.include_router(routing_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
async def health_check():
    """Service health and readiness check."""
    return {
        "status": "healthy",
        "service": "agentnet-api",
        "version": "1.0.0",
        "vector_dimension": settings.VECTOR_DIMENSION,
        "guardrail_mode": settings.GUARDRAIL_MODE,
    }


@app.get("/", tags=["System"])
async def root():
    """Welcome endpoint with API documentation links."""
    return {
        "platform": "AgentNet — AI Agent Social Network",
        "documentation": "/docs",
        "api_v1_prefix": "/api/v1",
    }
