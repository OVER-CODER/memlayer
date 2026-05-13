"""
Main FastAPI application entry point.
Production-ready with async lifecycle, health checks, and metrics.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
from app.api import workspaces, chats, memories, console
from app.core.config import settings

# Load environment variables from .env file
load_dotenv()

# Prometheus metrics import
try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Global state for startup
app_state = {
    "db_ready": False,
    "redis_ready": False,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Async lifecycle manager for production readiness."""
    logger.info("Starting MemLayer backend...")

    # Initialize database asynchronously
    try:
        from app.db.session import init_async_db

        await init_async_db()
        app_state["db_ready"] = True
        logger.info("✓ Database connection established")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        app_state["db_ready"] = False

    # Initialize Redis connection (graceful degradation)
    try:
        from app.runtime.coordination_cache import RuntimeCoordinationLayer

        redis = RuntimeCoordinationLayer()
        if redis.health_check():
            app_state["redis_ready"] = True
            logger.info("✓ Redis connection established")
        else:
            logger.warning("⚠ Redis health check failed - continuing degraded")
            app_state["redis_ready"] = False
    except Exception as e:
        logger.warning(f"⚠ Redis initialization failed - continuing degraded: {e}")
        app_state["redis_ready"] = False

    logger.info(
        f"Startup complete. DB: {app_state['db_ready']}, Redis: {app_state['redis_ready']}"
    )

    yield

    # Shutdown
    logger.info("Shutting down MemLayer backend...")
    app_state["db_ready"] = False
    app_state["redis_ready"] = False


# Create app with lifespan
app = FastAPI(
    title="MemLayer - Persistent Semantic Memory Runtime",
    description="Foundational memory system for AI workspaces",
    version="0.1.0",
    lifespan=lifespan,
)

# Add Middleware (Execution order is bottom-to-top)
from app.security.middleware.authentication import AuthenticationMiddleware
from app.security.middleware.tenant import TenantMiddleware

app.add_middleware(TenantMiddleware)
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(workspaces.router)
app.include_router(chats.router)
app.include_router(memories.router)
app.include_router(console.router)


@app.get("/health")
def health_check():
    """Basic liveness check."""
    return {"status": "healthy", "version": "0.1.0", "service": "memlayer-backend"}


@app.get("/health/ready")
async def health_ready():
    """Deep readiness check - verifies DB and Redis connectivity."""
    issues = []

    # Check database
    if not app_state["db_ready"]:
        issues.append("database_not_ready")

    # Check Redis
    if not app_state["redis_ready"]:
        issues.append("redis_not_ready")

    if issues:
        return {"status": "not_ready", "issues": issues, "version": "0.1.0"}

    return {
        "status": "ready",
        "database": "connected",
        "redis": "connected",
        "version": "0.1.0",
    }


@app.get("/metrics", tags=["observability"])
async def metrics():
    """Prometheus metrics endpoint."""
    if not PROMETHEUS_AVAILABLE:
        return PlainTextResponse("Prometheus client not available", status_code=503)

    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/config")
def get_config():
    """Get system configuration (non-sensitive)."""
    return {
        "embedding_model": settings.embedding_model,
        "embedding_dim": settings.embedding_dim,
        "gemini_model": settings.gemini_model,
        "top_k_memories": settings.top_k_memories,
        "memory_retrieval_threshold": settings.memory_retrieval_threshold,
        "deterministic_mode": settings.deterministic_mode,
    }


if __name__ == "__main__":
    import uvicorn

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(settings.port) if hasattr(settings, "port") else 8000,
        reload=settings.debug,
    )
