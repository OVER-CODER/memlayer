"""
Database connection and session management for MemLayer.
Supports both synchronous (legacy) and asynchronous (production) execution.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from typing import AsyncGenerator

# Synchronous Engine (Legacy/Background)
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Asynchronous Engine (Production Runtime)
async_engine = create_async_engine(
    settings.async_database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    # Standard settings for async drivers
    pool_size=20,
    max_overflow=10,
)
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=async_engine,
    class_=AsyncSession
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
    print("✓ Database tables created")
