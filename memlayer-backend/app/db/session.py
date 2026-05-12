"""
Database connection and session management for MemLayer.
Supports both synchronous (legacy) and asynchronous (production) execution.
"""

import logging
import socket
from urllib.parse import urlparse
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from typing import AsyncGenerator

logger = logging.getLogger(__name__)


def _resolve_host_to_ip(hostname: str) -> str:
    """Resolve hostname to IP address to avoid DNS issues in some environments."""
    try:
        ip = socket.gethostbyname(hostname)
        logger.info(f"Resolved {hostname} to {ip}")
        return ip
    except Exception as e:
        logger.warning(f"Could not resolve {hostname}: {e}")
        return hostname


def _convert_dsn_to_ip(dsn: str) -> str:
    """Convert a DSN with hostname to use IP address directly."""
    try:
        parsed = urlparse(dsn)
        if parsed.hostname and not parsed.hostname.replace(".", "").isdigit():
            ip = _resolve_host_to_ip(parsed.hostname)
            # Rebuild the DSN with IP
            port = f":{parsed.port}" if parsed.port else ""
            path = parsed.path if parsed.path else ""
            query = f"?{parsed.query}" if parsed.query else ""
            username = parsed.username or ""
            password = f":{parsed.password}" if parsed.password else ""
            at = "@" if username else ""
            return f"{parsed.scheme}://{username}{password}{at}{ip}{port}{path}{query}"
        return dsn
    except Exception as e:
        logger.warning(f"Could not convert DSN: {e}")
        return dsn


# Convert database URLs to use IP addresses
_db_url = _convert_dsn_to_ip(settings.database_url)
_async_db_url = _convert_dsn_to_ip(settings.async_database_url)

logger.info(f"Database URL: {_db_url}")
logger.info(f"Async Database URL: {_async_db_url}")

# Synchronous Engine (Legacy/Background)
engine = create_engine(
    _db_url,
    echo=settings.debug,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Asynchronous Engine (Production Runtime)
async_engine = create_async_engine(
    _async_db_url,
    echo=settings.debug,
    pool_pre_ping=True,
    # Standard settings for async drivers
    pool_size=20,
    max_overflow=10,
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
