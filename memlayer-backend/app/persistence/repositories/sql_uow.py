"""
SQLAlchemy Implementation of Unit of Work for MemLayer.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.persistence.unit_of_work import IUnitOfWork
from app.persistence.repositories.sql_repositories import (
    SQLWorkspaceRepository,
    SQLMemoryRepository,
    SQLReplayTraceRepository,
    SQLAuditRepository,
    SQLTelemetryRepository
)


class SQLUnitOfWork(IUnitOfWork):
    """
    SQLAlchemy implementation of the Unit of Work pattern.
    """

    def __init__(self, session: AsyncSession):
        self._session = session
        self.workspaces = SQLWorkspaceRepository(session)
        self.memories = SQLMemoryRepository(session)
        self.traces = SQLReplayTraceRepository(session)
        self.audit = SQLAuditRepository(session)
        self.telemetry = SQLTelemetryRepository(session)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        else:
            await self.commit()

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()
