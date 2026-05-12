"""
SQL-backed Repositories for MemLayer.
Implements the abstract repository contracts using SQLAlchemy AsyncSession.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert, update, desc
from app.persistence.interfaces import (
    IWorkspaceRepository,
    IMemoryRepository,
    IReplayTraceRepository,
    IAuditRepository,
    ITelemetryRepository
)
from app.db.models import (
    Workspace, Memory, ReplayTrace, GovernanceAudit, TelemetryEvent
)
from app.persistence.serialization import get_canonical_serializer

serializer = get_canonical_serializer()


class SQLWorkspaceRepository(IWorkspaceRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        stmt = select(Workspace).where(Workspace.id == id, Workspace.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        ws = result.scalar_one_or_none()
        return serializer.to_dict(ws) if ws else None

    async def get_by_name(self, name: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        stmt = select(Workspace).where(Workspace.name == name, Workspace.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        ws = result.scalar_one_or_none()
        return serializer.to_dict(ws) if ws else None

    async def list(self, tenant_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        stmt = select(Workspace).where(Workspace.tenant_id == tenant_id).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return [serializer.to_dict(ws) for ws in result.scalars().all()]

    async def save(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation for save (upsert)
        ws_id = entity.get("id")
        tenant_id = entity.get("tenant_id", "default")
        
        if ws_id:
            # Try to update
            stmt = update(Workspace).where(
                Workspace.id == ws_id, 
                Workspace.tenant_id == tenant_id
            ).values(**entity).returning(Workspace)
            result = await self.session.execute(stmt)
            ws = result.scalar_one_or_none()
            if ws:
                return serializer.to_dict(ws)
        
        # Insert new
        stmt = insert(Workspace).values(**entity).returning(Workspace)
        result = await self.session.execute(stmt)
        ws = result.scalar_one()
        return serializer.to_dict(ws)

    async def delete(self, id: str, tenant_id: str) -> bool:
        stmt = delete(Workspace).where(Workspace.id == id, Workspace.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0


class SQLMemoryRepository(IMemoryRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        stmt = select(Memory).where(Memory.id == id, Memory.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        m = result.scalar_one_or_none()
        return serializer.to_dict(m) if m else None

    async def list(self, tenant_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        stmt = select(Memory).where(Memory.tenant_id == tenant_id).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return [serializer.to_dict(m) for m in result.scalars().all()]

    async def save(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        stmt = insert(Memory).values(**entity).returning(Memory)
        result = await self.session.execute(stmt)
        m = result.scalar_one()
        return serializer.to_dict(m)

    async def delete(self, id: str, tenant_id: str) -> bool:
        stmt = delete(Memory).where(Memory.id == id, Memory.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def search_semantic(
        self, 
        workspace_id: str, 
        query_vector: List[float], 
        tenant_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        # This assumes pgvector is available
        # stmt = select(Memory).where(
        #     Memory.workspace_id == workspace_id,
        #     Memory.tenant_id == tenant_id
        # ).order_by(Memory.embedding.cosine_distance(query_vector)).limit(limit)
        
        # Fallback for local testing without pgvector
        stmt = select(Memory).where(
            Memory.workspace_id == workspace_id,
            Memory.tenant_id == tenant_id
        ).limit(limit)
        result = await self.session.execute(stmt)
        return [serializer.to_dict(m) for m in result.scalars().all()]

    async def get_by_workspace(self, workspace_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        stmt = select(Memory).where(
            Memory.workspace_id == workspace_id,
            Memory.tenant_id == tenant_id
        )
        result = await self.session.execute(stmt)
        return [serializer.to_dict(m) for m in result.scalars().all()]


class SQLReplayTraceRepository(IReplayTraceRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_trace(self, trace_data: Dict[str, Any]) -> str:
        # Ensure canonical serialization of JSON fields
        trace_data["execution_plan"] = serializer.to_dict(trace_data.get("execution_plan", {}))
        trace_data["trace_data"] = serializer.to_dict(trace_data.get("trace_data", {}))
        
        stmt = insert(ReplayTrace).values(**trace_data).returning(ReplayTrace.trace_id)
        result = await self.session.execute(stmt)
        return str(result.scalar_one())

    async def get_trace(self, trace_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        stmt = select(ReplayTrace).where(
            ReplayTrace.trace_id == trace_id, 
            ReplayTrace.tenant_id == tenant_id
        )
        result = await self.session.execute(stmt)
        t = result.scalar_one_or_none()
        return serializer.to_dict(t) if t else None

    async def list_traces(
        self, 
        workspace_id: str, 
        tenant_id: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        stmt = select(ReplayTrace).where(
            ReplayTrace.workspace_id == workspace_id,
            ReplayTrace.tenant_id == tenant_id
        ).order_by(desc(ReplayTrace.timestamp)).limit(limit)
        result = await self.session.execute(stmt)
        return [serializer.to_dict(t) for t in result.scalars().all()]


class SQLAuditRepository(IAuditRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def append_event(self, event_data: Dict[str, Any]) -> str:
        event_data["event_data"] = serializer.to_dict(event_data.get("event_data", {}))
        stmt = insert(GovernanceAudit).values(**event_data).returning(GovernanceAudit.audit_id)
        result = await self.session.execute(stmt)
        return str(result.scalar_one())

    async def get_trail(
        self, 
        workspace_id: str, 
        tenant_id: str, 
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        stmt = select(GovernanceAudit).where(
            GovernanceAudit.workspace_id == workspace_id,
            GovernanceAudit.tenant_id == tenant_id
        ).order_by(desc(GovernanceAudit.timestamp)).limit(limit)
        result = await self.session.execute(stmt)
        return [serializer.to_dict(a) for a in result.scalars().all()]


class SQLTelemetryRepository(ITelemetryRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_metric(self, metric_data: Dict[str, Any]) -> None:
        metric_data["token_metrics"] = serializer.to_dict(metric_data.get("token_metrics", {}))
        stmt = insert(TelemetryEvent).values(**metric_data)
        await self.session.execute(stmt)

    async def get_metrics(
        self, 
        trace_id: str, 
        tenant_id: str
    ) -> List[Dict[str, Any]]:
        stmt = select(TelemetryEvent).where(
            TelemetryEvent.trace_id == trace_id,
            TelemetryEvent.tenant_id == tenant_id
        ).order_by(TelemetryEvent.timestamp)
        result = await self.session.execute(stmt)
        return [serializer.to_dict(e) for e in result.scalars().all()]
