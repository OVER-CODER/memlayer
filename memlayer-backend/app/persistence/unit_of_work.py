"""
Unit of Work Pattern for MemLayer Persistence.

Coordinates multiple repositories to ensure atomicity of cognition
commit cycles, especially for replay traces and governance updates.
"""

from abc import ABC, abstractmethod
from typing import Optional
from app.persistence.interfaces import (
    IWorkspaceRepository,
    IMemoryRepository,
    IReplayTraceRepository,
    IAuditRepository,
    ITelemetryRepository
)


class IUnitOfWork(ABC):
    """
    Interface for the Unit of Work.
    
    Ensures that all changes in a single cognition execution (compilation + trace + audit)
    are committed atomically or rolled back together.
    """
    
    workspaces: IWorkspaceRepository
    memories: IMemoryRepository
    traces: IReplayTraceRepository
    audit: IAuditRepository
    telemetry: ITelemetryRepository

    @abstractmethod
    async def __aenter__(self):
        """Start a transaction."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Finalize the transaction."""
        pass

    @abstractmethod
    async def commit(self):
        """Commit the work."""
        pass

    @abstractmethod
    async def rollback(self):
        """Rollback the work."""
        pass
