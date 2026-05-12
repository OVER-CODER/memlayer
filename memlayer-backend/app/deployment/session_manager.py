"""Runtime Session Manager for Phase 9.

Manages persistent runtime sessions, lifecycle tracking, checkpointing,
and restart recovery. All session state is serializable for recovery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    TERMINATED = "terminated"
    RECOVERING = "recovering"


@dataclass
class RuntimeSession:
    """A runtime session tracking coordination lifecycle."""

    session_id: str
    tenant_id: str = "default"
    workspace_ids: List[str] = field(default_factory=list)
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    coordination_count: int = 0
    total_tokens_consumed: int = 0
    checkpoint_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "tenant_id": self.tenant_id,
            "workspace_ids": self.workspace_ids,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "coordination_count": self.coordination_count,
            "total_tokens_consumed": self.total_tokens_consumed,
            "checkpoint_ids": self.checkpoint_ids,
        }


class RuntimeSessionManager:
    """Manages runtime session lifecycle, checkpointing, and recovery.

    Sessions track:
    - Active workspaces
    - Coordination counts
    - Token consumption
    - Checkpoint references for recovery
    """

    def __init__(self, timeout_seconds: int = 3600):
        self._sessions: Dict[str, RuntimeSession] = {}
        self._timeout = timeout_seconds

    def create_session(
        self,
        tenant_id: str = "default",
        session_id: Optional[str] = None,
        workspace_ids: Optional[List[str]] = None,
    ) -> RuntimeSession:
        """Create a new runtime session."""
        sid = session_id or f"sess-{uuid.uuid4().hex[:10]}"
        session = RuntimeSession(
            session_id=sid,
            tenant_id=tenant_id,
            workspace_ids=workspace_ids or [],
        )
        self._sessions[sid] = session
        return session

    def get_session(self, session_id: str) -> Optional[RuntimeSession]:
        return self._sessions.get(session_id)

    def record_activity(
        self,
        session_id: str,
        tokens_consumed: int = 0,
        coordination: bool = False,
    ) -> None:
        """Record activity on a session."""
        session = self._sessions.get(session_id)
        if not session:
            return
        session.last_activity = datetime.now(timezone.utc)
        session.total_tokens_consumed += tokens_consumed
        if coordination:
            session.coordination_count += 1

    def add_checkpoint(self, session_id: str, checkpoint_id: str) -> None:
        """Record a checkpoint reference on a session."""
        session = self._sessions.get(session_id)
        if session:
            session.checkpoint_ids.append(checkpoint_id)

    def pause_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False
        session.status = SessionStatus.PAUSED
        return True

    def terminate_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False
        session.status = SessionStatus.TERMINATED
        return True

    def mark_recovering(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False
        session.status = SessionStatus.RECOVERING
        return True

    def resume_session(self, session_id: str) -> bool:
        """Resume a paused or recovering session."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        if session.status in (SessionStatus.PAUSED, SessionStatus.RECOVERING):
            session.status = SessionStatus.ACTIVE
            session.last_activity = datetime.now(timezone.utc)
            return True
        return False

    def get_active_sessions(self, tenant_id: Optional[str] = None) -> List[RuntimeSession]:
        """Get all active sessions, optionally filtered by tenant."""
        sessions = [
            s for s in self._sessions.values()
            if s.status == SessionStatus.ACTIVE
        ]
        if tenant_id:
            sessions = [s for s in sessions if s.tenant_id == tenant_id]
        return sessions

    def get_session_metrics(self) -> Dict[str, Any]:
        by_status = {}
        for s in self._sessions.values():
            by_status[s.status.value] = by_status.get(s.status.value, 0) + 1

        return {
            "total_sessions": len(self._sessions),
            "by_status": by_status,
            "total_tokens_consumed": sum(s.total_tokens_consumed for s in self._sessions.values()),
            "total_coordinations": sum(s.coordination_count for s in self._sessions.values()),
        }

    def export_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Export session state for recovery."""
        session = self._sessions.get(session_id)
        if not session:
            return None
        return session.to_dict()
