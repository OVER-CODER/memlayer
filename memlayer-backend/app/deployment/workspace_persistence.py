"""Workspace Persistence Manager for Phase 9.

Deterministic serialization and persistence of semantic workspaces,
projections, coordination traces, and runtime metadata. All persistence
is replay-compatible and version-safe.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib
import json
import os

from app.deployment.deployment_config import PersistenceConfig


@dataclass
class PersistedWorkspace:
    """Serializable workspace state."""

    workspace_id: str
    tenant_id: str = "default"
    memories: List[Dict[str, Any]] = field(default_factory=list)
    provider: str = "claude"
    token_budget: int = 4000
    metadata: Dict[str, Any] = field(default_factory=dict)
    coordination_history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    version: int = 1
    checksum: str = ""

    def compute_checksum(self) -> str:
        payload = json.dumps({
            "workspace_id": self.workspace_id,
            "tenant_id": self.tenant_id,
            "memory_count": len(self.memories),
            "provider": self.provider,
            "version": self.version,
        }, sort_keys=True)
        self.checksum = hashlib.sha256(payload.encode()).hexdigest()[:20]
        return self.checksum

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "tenant_id": self.tenant_id,
            "memories": self.memories,
            "provider": self.provider,
            "token_budget": self.token_budget,
            "metadata": self.metadata,
            "coordination_history": self.coordination_history,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "checksum": self.checksum,
        }


class WorkspacePersistenceManager:
    """Manages workspace state persistence and loading.

    All serialization is deterministic and replay-compatible.
    Supports both filesystem and in-memory storage.
    """

    def __init__(self, config: Optional[PersistenceConfig] = None):
        self._config = config or PersistenceConfig()
        self._store: Dict[str, PersistedWorkspace] = {}
        self._persist_log: List[Dict[str, Any]] = []

    def persist(self, workspace: PersistedWorkspace) -> Dict[str, Any]:
        """Persist a workspace state."""
        workspace.updated_at = datetime.now(timezone.utc).isoformat()
        if not workspace.created_at:
            workspace.created_at = workspace.updated_at
        workspace.compute_checksum()

        self._store[workspace.workspace_id] = workspace

        # Filesystem persistence if configured
        if self._config.auto_persist:
            self._write_to_storage(workspace)

        record = {
            "action": "persist",
            "workspace_id": workspace.workspace_id,
            "version": workspace.version,
            "checksum": workspace.checksum,
            "memory_count": len(workspace.memories),
            "timestamp": workspace.updated_at,
        }
        self._persist_log.append(record)
        return record

    def load(self, workspace_id: str) -> Optional[PersistedWorkspace]:
        """Load a workspace from storage."""
        # Try in-memory first
        ws = self._store.get(workspace_id)
        if ws:
            return ws

        # Try filesystem
        return self._read_from_storage(workspace_id)

    def exists(self, workspace_id: str) -> bool:
        """Check if a workspace exists."""
        if workspace_id in self._store:
            return True
        path = self._workspace_path(workspace_id)
        return os.path.exists(path)

    def delete(self, workspace_id: str) -> bool:
        """Delete a persisted workspace."""
        deleted = workspace_id in self._store
        self._store.pop(workspace_id, None)

        path = self._workspace_path(workspace_id)
        if os.path.exists(path):
            os.remove(path)
            deleted = True

        if deleted:
            self._persist_log.append({
                "action": "delete",
                "workspace_id": workspace_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        return deleted

    def list_workspaces(self, tenant_id: Optional[str] = None) -> List[str]:
        """List persisted workspace IDs."""
        if tenant_id:
            return [
                ws_id for ws_id, ws in self._store.items()
                if ws.tenant_id == tenant_id
            ]
        return list(self._store.keys())

    def verify_integrity(self, workspace_id: str) -> Dict[str, Any]:
        """Verify persistence integrity of a workspace."""
        ws = self.load(workspace_id)
        if not ws:
            return {"valid": False, "reason": "not_found"}

        stored_checksum = ws.checksum
        ws.compute_checksum()
        return {
            "valid": stored_checksum == ws.checksum,
            "stored_checksum": stored_checksum,
            "computed_checksum": ws.checksum,
            "workspace_id": workspace_id,
            "version": ws.version,
        }

    def get_persistence_metrics(self) -> Dict[str, Any]:
        """Get persistence layer metrics."""
        return {
            "total_workspaces": len(self._store),
            "total_persist_operations": len(self._persist_log),
            "persist_log": self._persist_log[-20:],
        }

    # -----------------------------------------------------------------
    # Storage I/O
    # -----------------------------------------------------------------

    def _workspace_path(self, workspace_id: str) -> str:
        return os.path.join(self._config.storage_dir, f"{workspace_id}.json")

    def _write_to_storage(self, workspace: PersistedWorkspace) -> None:
        os.makedirs(self._config.storage_dir, exist_ok=True)
        path = self._workspace_path(workspace.workspace_id)
        with open(path, "w") as f:
            json.dump(workspace.to_dict(), f, indent=2, default=str)

    def _read_from_storage(self, workspace_id: str) -> Optional[PersistedWorkspace]:
        path = self._workspace_path(workspace_id)
        if not os.path.exists(path):
            return None
        with open(path) as f:
            data = json.load(f)
        ws = PersistedWorkspace(**{k: v for k, v in data.items() if k != "checksum"})
        ws.checksum = data.get("checksum", "")
        return ws
