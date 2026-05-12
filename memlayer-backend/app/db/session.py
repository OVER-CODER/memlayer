"""
Database connection and session management for MemLayer.
Supports both synchronous (legacy) and asynchronous (production) execution.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from typing import AsyncGenerator

# Configure logging early so we see startup messages
logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Use direct URLs - remove query params that asyncpg doesn't support
from urllib.parse import urlparse, urlunparse


def _clean_dsn_for_asyncpg(dsn: str) -> str:
    """Remove sslmode from DSN as asyncpg handles SSL differently."""
    try:
        parsed = urlparse(dsn)
        # Remove sslmode from query
        query_parts = parsed.query.split("&") if parsed.query else []
        query_parts = [q for q in query_parts if not q.startswith("sslmode=")]
        new_query = "&".join(query_parts)
        result = urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment)
        )
        return result
    except Exception:
        return dsn


_db_url = settings.database_url
_async_db_url = _clean_dsn_for_asyncpg(settings.async_database_url)

logger.info(f"Database URL: {_db_url}")
logger.info(f"Async Database URL (cleaned): {_async_db_url}")

# Synchronous Engine (Legacy/Background)
engine = create_engine(
    _db_url,
    echo=settings.debug,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Asynchronous Engine (Production Runtime)
# Pass ssl as connect_arg since asyncpg handles it differently
async_engine = create_async_engine(
    _async_db_url,
    echo=settings.debug,
    pool_pre_ping=True,
    connect_args={"ssl": "require"},
    pool_size=5,
    max_overflow=5,
    pool_timeout=30,
)
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession
)


def get_db() -> Session:
    """Dependency for getting synchronous DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting asynchronous DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def init_db():
    """Initialize the database with all tables (Synchronous)."""
    from app.db.models import Base

    Base.metadata.create_all(bind=engine)
    logger.info("✓ Database tables created (sync)")


async def init_async_db():
    """Initialize the database asynchronously with connection verification."""
    from app.db.models import Base

    max_retries = 5
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            # Test connection
            async with async_engine.connect() as conn:
                await conn.execute("SELECT 1")

            # Create tables
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info("✓ Database initialized and verified (async)")
            return

        except Exception as e:
            logger.warning(
                f"Database init attempt {attempt + 1}/{max_retries} failed: {e}"
            )
            if attempt < max_retries - 1:
                import asyncio

                await asyncio.sleep(retry_delay)
            else:
                raise Exception(
                    f"Failed to initialize database after {max_retries} attempts: {e}"
                )
