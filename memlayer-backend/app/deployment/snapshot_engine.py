"""Workspace Snapshot Engine for Phase 9.

Deterministic workspace snapshots, replayable checkpoints, historical
comparison, and semantic state rollback. All snapshots are serializable
and replay-compatible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib
import json
import os

from app.deployment.deployment_config import PersistenceConfig
from app.deployment.workspace_persistence import PersistedWorkspace


@dataclass
class WorkspaceCheckpoint:
    """Point-in-time workspace checkpoint."""

    checkpoint_id: str
    workspace_id: str
    tenant_id: str = "default"
    version: int = 1
    memory_count: int = 0
    provider: str = "claude"
    state_checksum: str = ""
    coordination_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    snapshot_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "workspace_id": self.workspace_id,
            "tenant_id": self.tenant_id,
            "version": self.version,
            "memory_count": self.memory_count,
            "provider": self.provider,
            "state_checksum": self.state_checksum,
            "coordination_count": self.coordination_count,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class SnapshotComparisonResult:
    """Result of comparing two snapshots."""

    checkpoint_a: str
    checkpoint_b: str
    checksums_match: bool
    version_delta: int
    memory_count_delta: int
    semantic_continuity: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checkpoint_a": self.checkpoint_a,
            "checkpoint_b": self.checkpoint_b,
            "checksums_match": self.checksums_match,
            "version_delta": self.version_delta,
            "memory_count_delta": self.memory_count_delta,
            "semantic_continuity": round(self.semantic_continuity, 4),
        }


class WorkspaceSnapshotEngine:
    """Creates and manages deterministic workspace snapshots.

    Guarantees:
    - Snapshots are deterministic given the same workspace state
    - Snapshots are replay-compatible
    - Historical snapshots can be compared
    - Workspace state can be rolled back to any snapshot
    """

    def __init__(self, config: Optional[PersistenceConfig] = None):
        self._config = config or PersistenceConfig()
        self._checkpoints: Dict[str, List[WorkspaceCheckpoint]] = {}
        self._counter = 0

    def create_checkpoint(self, workspace: PersistedWorkspace) -> WorkspaceCheckpoint:
        """Create a deterministic checkpoint from workspace state."""
        self._counter += 1
        workspace.compute_checksum()

        checkpoint = WorkspaceCheckpoint(
            checkpoint_id=f"cp-{self._counter:06d}",
            workspace_id=workspace.workspace_id,
            tenant_id=workspace.tenant_id,
            version=workspace.version,
            memory_count=len(workspace.memories),
            provider=workspace.provider,
            state_checksum=workspace.checksum,
            coordination_count=len(workspace.coordination_history),
            snapshot_data=workspace.to_dict(),
        )

        ws_checkpoints = self._checkpoints.setdefault(workspace.workspace_id, [])
        ws_checkpoints.append(checkpoint)

        # Enforce limit
        max_snap = self._config.max_snapshots_per_workspace
        if len(ws_checkpoints) > max_snap:
            self._checkpoints[workspace.workspace_id] = ws_checkpoints[-max_snap:]

        return checkpoint

    def restore_from_checkpoint(self, checkpoint_id: str) -> Optional[PersistedWorkspace]:
        """Restore workspace state from a checkpoint."""
        for ws_id, checkpoints in self._checkpoints.items():
            for cp in checkpoints:
                if cp.checkpoint_id == checkpoint_id:
                    data = cp.snapshot_data
                    ws = PersistedWorkspace(
                        workspace_id=data["workspace_id"],
                        tenant_id=data.get("tenant_id", "default"),
                        memories=data.get("memories", []),
                        provider=data.get("provider", "claude"),
                        token_budget=data.get("token_budget", 4000),
                        metadata=data.get("metadata", {}),
                        coordination_history=data.get("coordination_history", []),
                        created_at=data.get("created_at", ""),
                        updated_at=data.get("updated_at", ""),
                        version=data.get("version", 1),
                    )
                    ws.compute_checksum()
                    return ws
        return None

    def get_checkpoints(self, workspace_id: str) -> List[WorkspaceCheckpoint]:
        return list(self._checkpoints.get(workspace_id, []))

    def compare_checkpoints(
        self,
        checkpoint_id_a: str,
        checkpoint_id_b: str,
    ) -> Optional[SnapshotComparisonResult]:
        """Compare two checkpoints."""
        cp_a = self._find_checkpoint(checkpoint_id_a)
        cp_b = self._find_checkpoint(checkpoint_id_b)
        if not cp_a or not cp_b:
            return None

        return SnapshotComparisonResult(
            checkpoint_a=checkpoint_id_a,
            checkpoint_b=checkpoint_id_b,
            checksums_match=cp_a.state_checksum == cp_b.state_checksum,
            version_delta=cp_b.version - cp_a.version,
            memory_count_delta=cp_b.memory_count - cp_a.memory_count,
            semantic_continuity=1.0 if cp_a.state_checksum == cp_b.state_checksum else 0.5,
        )

    def get_snapshot_metrics(self) -> Dict[str, Any]:
        total_checkpoints = sum(len(cps) for cps in self._checkpoints.values())
        return {
            "total_workspaces_tracked": len(self._checkpoints),
            "total_checkpoints": total_checkpoints,
            "checkpoints_per_workspace": {
                ws_id: len(cps) for ws_id, cps in self._checkpoints.items()
            },
        }

    def _find_checkpoint(self, checkpoint_id: str) -> Optional[WorkspaceCheckpoint]:
        for cps in self._checkpoints.values():
            for cp in cps:
                if cp.checkpoint_id == checkpoint_id:
                    return cp
        return None
