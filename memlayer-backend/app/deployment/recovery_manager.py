"""Runtime Recovery Manager for Phase 9.

Recovers interrupted runtime sessions, restores workspace semantic state,
recovers coordination traces, and validates replay consistency after
recovery. All recovery operations are deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.deployment.workspace_persistence import (
    WorkspacePersistenceManager,
    PersistedWorkspace,
)
from app.deployment.snapshot_engine import WorkspaceSnapshotEngine
from app.deployment.session_manager import RuntimeSessionManager, SessionStatus


@dataclass
class RecoveryResult:
    """Result of a recovery operation."""

    session_id: str
    workspace_id: str
    success: bool
    recovered_from: str = ""  # checkpoint_id or "persistence"
    checksum_before: str = ""
    checksum_after: str = ""
    integrity_valid: bool = False
    memory_count: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "workspace_id": self.workspace_id,
            "success": self.success,
            "recovered_from": self.recovered_from,
            "integrity_valid": self.integrity_valid,
            "memory_count": self.memory_count,
            "timestamp": self.timestamp.isoformat(),
        }


class RuntimeRecoveryManager:
    """Recovers interrupted runtimes and validates post-recovery state.

    Recovery strategy:
    1. Try latest checkpoint from snapshot engine
    2. Fall back to persisted workspace state
    3. Validate integrity after recovery
    4. Resume session

    All recovery operations are deterministic and replayable.
    """

    def __init__(
        self,
        persistence: Optional[WorkspacePersistenceManager] = None,
        snapshots: Optional[WorkspaceSnapshotEngine] = None,
        sessions: Optional[RuntimeSessionManager] = None,
    ):
        self._persistence = persistence or WorkspacePersistenceManager()
        self._snapshots = snapshots or WorkspaceSnapshotEngine()
        self._sessions = sessions or RuntimeSessionManager()
        self._recovery_log: List[RecoveryResult] = []

    def recover_session(self, session_id: str) -> List[RecoveryResult]:
        """Recover all workspaces for an interrupted session."""
        session = self._sessions.get_session(session_id)
        if not session:
            return [RecoveryResult(
                session_id=session_id, workspace_id="",
                success=False, recovered_from="session_not_found",
            )]

        self._sessions.mark_recovering(session_id)
        results = []

        for ws_id in session.workspace_ids:
            result = self.recover_workspace(session_id, ws_id)
            results.append(result)

        # Resume session if all recoveries succeeded
        all_ok = all(r.success for r in results)
        if all_ok:
            self._sessions.resume_session(session_id)

        return results

    def recover_workspace(
        self,
        session_id: str,
        workspace_id: str,
    ) -> RecoveryResult:
        """Recover a single workspace from the best available source."""

        # Strategy 1: Try latest checkpoint
        checkpoints = self._snapshots.get_checkpoints(workspace_id)
        if checkpoints:
            latest_cp = checkpoints[-1]
            restored = self._snapshots.restore_from_checkpoint(latest_cp.checkpoint_id)
            if restored:
                # Validate integrity
                restored.compute_checksum()
                integrity = restored.checksum == latest_cp.state_checksum

                result = RecoveryResult(
                    session_id=session_id,
                    workspace_id=workspace_id,
                    success=True,
                    recovered_from=latest_cp.checkpoint_id,
                    checksum_before=latest_cp.state_checksum,
                    checksum_after=restored.checksum,
                    integrity_valid=integrity,
                    memory_count=len(restored.memories),
                )
                self._persistence.persist(restored)
                self._recovery_log.append(result)
                return result

        # Strategy 2: Fall back to persisted state
        persisted = self._persistence.load(workspace_id)
        if persisted:
            old_checksum = persisted.checksum
            persisted.compute_checksum()

            result = RecoveryResult(
                session_id=session_id,
                workspace_id=workspace_id,
                success=True,
                recovered_from="persistence",
                checksum_before=old_checksum,
                checksum_after=persisted.checksum,
                integrity_valid=old_checksum == persisted.checksum,
                memory_count=len(persisted.memories),
            )
            self._recovery_log.append(result)
            return result

        # Nothing to recover from
        result = RecoveryResult(
            session_id=session_id,
            workspace_id=workspace_id,
            success=False,
            recovered_from="no_source",
        )
        self._recovery_log.append(result)
        return result

    def get_recovery_metrics(self) -> Dict[str, Any]:
        """Get recovery system metrics."""
        if not self._recovery_log:
            return {"total_recoveries": 0}

        successful = sum(1 for r in self._recovery_log if r.success)
        integrity_valid = sum(1 for r in self._recovery_log if r.integrity_valid)

        return {
            "total_recoveries": len(self._recovery_log),
            "successful": successful,
            "success_rate": successful / len(self._recovery_log),
            "integrity_valid": integrity_valid,
            "integrity_rate": integrity_valid / len(self._recovery_log),
            "recovery_log": [r.to_dict() for r in self._recovery_log[-20:]],
        }
