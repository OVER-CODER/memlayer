"""Workspace API for Phase 8.

Provides workspace lifecycle management: creation, loading, state updates,
metadata inspection, and diagnostics. All operations are deterministic
and replay-compatible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib
import uuid


@dataclass
class WorkspaceConfig:
    """Configuration for a workspace."""

    workspace_id: Optional[str] = None
    default_provider: str = "claude"
    token_budget: int = 4000
    query_type: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkspaceSnapshot:
    """Point-in-time workspace state snapshot."""

    workspace_id: str
    memory_count: int
    state_checksum: str
    provider: str
    token_budget: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "memory_count": self.memory_count,
            "state_checksum": self.state_checksum,
            "provider": self.provider,
            "token_budget": self.token_budget,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


class WorkspaceAPI:
    """Manages workspace lifecycle and semantic state.

    Workspaces are the unit of semantic cognition — each workspace
    holds memories and produces compiled projections.
    """

    def __init__(self):
        self._workspaces: Dict[str, Dict[str, Any]] = {}
        self._snapshots: Dict[str, List[WorkspaceSnapshot]] = {}

    def create_workspace(
        self,
        config: Optional[WorkspaceConfig] = None,
    ) -> WorkspaceSnapshot:
        """Create a new workspace."""
        cfg = config or WorkspaceConfig()
        ws_id = cfg.workspace_id or f"ws-{uuid.uuid4().hex[:12]}"

        self._workspaces[ws_id] = {
            "workspace_id": ws_id,
            "memories": [],
            "provider": cfg.default_provider,
            "token_budget": cfg.token_budget,
            "query_type": cfg.query_type,
            "metadata": cfg.metadata,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        snapshot = self._create_snapshot(ws_id)
        return snapshot

    def get_workspace(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve workspace metadata."""
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return None
        return {
            "workspace_id": ws["workspace_id"],
            "provider": ws["provider"],
            "token_budget": ws["token_budget"],
            "memory_count": len(ws["memories"]),
            "metadata": ws["metadata"],
            "created_at": ws["created_at"].isoformat(),
            "updated_at": ws["updated_at"].isoformat(),
        }

    def add_memories(self, workspace_id: str, memories: List[Any]) -> WorkspaceSnapshot:
        """Add memories to a workspace."""
        ws = self._workspaces.get(workspace_id)
        if not ws:
            raise ValueError(f"Workspace {workspace_id} not found")

        ws["memories"].extend(memories)
        ws["updated_at"] = datetime.now(timezone.utc)
        return self._create_snapshot(workspace_id)

    def get_memories(self, workspace_id: str) -> List[Any]:
        """Retrieve all memories from a workspace."""
        ws = self._workspaces.get(workspace_id)
        if not ws:
            raise ValueError(f"Workspace {workspace_id} not found")
        return list(ws["memories"])

    def update_config(
        self,
        workspace_id: str,
        provider: Optional[str] = None,
        token_budget: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkspaceSnapshot:
        """Update workspace configuration."""
        ws = self._workspaces.get(workspace_id)
        if not ws:
            raise ValueError(f"Workspace {workspace_id} not found")

        if provider is not None:
            ws["provider"] = provider
        if token_budget is not None:
            ws["token_budget"] = token_budget
        if metadata is not None:
            ws["metadata"].update(metadata)
        ws["updated_at"] = datetime.now(timezone.utc)

        return self._create_snapshot(workspace_id)

    def get_diagnostics(self, workspace_id: str) -> Dict[str, Any]:
        """Retrieve workspace diagnostics."""
        ws = self._workspaces.get(workspace_id)
        if not ws:
            raise ValueError(f"Workspace {workspace_id} not found")

        snapshots = self._snapshots.get(workspace_id, [])
        return {
            "workspace_id": workspace_id,
            "memory_count": len(ws["memories"]),
            "snapshot_count": len(snapshots),
            "provider": ws["provider"],
            "token_budget": ws["token_budget"],
            "created_at": ws["created_at"].isoformat(),
            "updated_at": ws["updated_at"].isoformat(),
            "state_checksums": [s.state_checksum for s in snapshots[-10:]],
        }

    def list_workspaces(self) -> List[Dict[str, Any]]:
        """List all workspace summaries."""
        return [self.get_workspace(ws_id) for ws_id in self._workspaces]

    def _create_snapshot(self, workspace_id: str) -> WorkspaceSnapshot:
        ws = self._workspaces[workspace_id]
        checksum = hashlib.sha256(
            f"{workspace_id}|{len(ws['memories'])}|{ws['provider']}|{ws['token_budget']}".encode()
        ).hexdigest()[:16]

        snapshot = WorkspaceSnapshot(
            workspace_id=workspace_id,
            memory_count=len(ws["memories"]),
            state_checksum=checksum,
            provider=ws["provider"],
            token_budget=ws["token_budget"],
            metadata=dict(ws["metadata"]),
        )
        self._snapshots.setdefault(workspace_id, []).append(snapshot)
        return snapshot
