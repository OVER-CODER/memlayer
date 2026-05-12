"""
Persistence Repository Interfaces for MemLayer.

Defines the abstract contracts for all storage domains, decoupling
the runtime from specific database implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Generic, TypeVar
from datetime import datetime

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """Generic repository interface."""

    @abstractmethod
    async def get_by_id(self, id: str, tenant_id: str) -> Optional[T]:
        """Retrieve a record by ID and tenant isolation."""
        pass

    @abstractmethod
    async def list(self, tenant_id: str, limit: int = 100, offset: int = 0) -> List[T]:
        """List records for a tenant."""
        pass

    @abstractmethod
    async def save(self, entity: T) -> T:
        """Save (create or update) a record."""
        pass

    @abstractmethod
    async def delete(self, id: str, tenant_id: str) -> bool:
        """Delete a record by ID and tenant isolation."""
        pass


class IWorkspaceRepository(IRepository[Dict[str, Any]]):
    """Interface for Workspace persistence."""

    @abstractmethod
    async def get_by_name(self, name: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Find workspace by name."""
        pass


class IMemoryRepository(IRepository[Dict[str, Any]]):
    """Interface for Semantic Memory persistence."""

    @abstractmethod
    async def search_semantic(
        self, 
        workspace_id: str, 
        query_vector: List[float], 
        tenant_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search."""
        pass

    @abstractmethod
    async def get_by_workspace(self, workspace_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        """Retrieve all memories for a workspace."""
        pass


class IReplayTraceRepository(ABC):
    """Interface for Replay Trace persistence (Immutable Append)."""

    @abstractmethod
    async def save_trace(self, trace_data: Dict[str, Any]) -> str:
        """Append a new replay trace."""
        pass

    @abstractmethod
    async def get_trace(self, trace_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific trace."""
        pass

    @abstractmethod
    async def list_traces(
        self, 
        workspace_id: str, 
        tenant_id: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List traces for a workspace."""
        pass


class IAuditRepository(ABC):
    """Interface for Governance Audit persistence (Immutable Append)."""

    @abstractmethod
    async def append_event(self, event_data: Dict[str, Any]) -> str:
        """Append an immutable audit event."""
        pass

    @abstractmethod
    async def get_trail(
        self, 
        workspace_id: str, 
        tenant_id: str, 
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Retrieve audit trail."""
        pass


class ITelemetryRepository(ABC):
    """Interface for Telemetry persistence (Time-Series)."""

    @abstractmethod
    async def record_metric(self, metric_data: Dict[str, Any]) -> None:
        """Record a telemetry metric."""
        pass

    @abstractmethod
    async def get_metrics(
        self, 
        trace_id: str, 
        tenant_id: str
    ) -> List[Dict[str, Any]]:
        """Retrieve metrics for a trace."""
        pass
