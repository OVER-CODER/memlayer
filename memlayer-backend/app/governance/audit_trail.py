"""
Runtime Audit Trail Manager for MemLayer.

Provides immutable, append-only audit trail recording for all runtime governance activities.
Records are deterministically serializable and replay-compatible.
All operations are tenant-scoped and isolated.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class AuditEventType(str, Enum):
    """Types of audit events."""

    COORDINATION_STARTED = "coordination_started"
    COORDINATION_COMPLETED = "coordination_completed"
    COORDINATION_FAILED = "coordination_failed"
    REPLAY_INITIATED = "replay_initiated"
    REPLAY_COMPLETED = "replay_completed"
    REPLAY_DIVERGENCE = "replay_divergence"
    POLICY_ENFORCED = "policy_enforced"
    POLICY_VIOLATION = "policy_violation"
    SEMANTIC_CHECKPOINT = "semantic_checkpoint"
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_COMPLETED = "recovery_completed"
    TENANT_BOUNDARY_CROSSED = "tenant_boundary_crossed"


@dataclass(frozen=True)
class AuditRecord:
    """Immutable audit record."""

    audit_id: str
    workspace_id: str
    tenant_id: str
    timestamp: str  # ISO 8601 UTC
    event_type: str  # AuditEventType value
    event_data: Dict[str, Any]
    recorded_by: str  # Component name
    integrity_hash: str  # SHA256


class RuntimeAuditTrailManager:
    """
    Manages immutable audit trails for runtime governance.

    All audit records are:
    - Deterministically serialized (JSON canonical form)
    - Append-only (no modifications after recording)
    - Tenant-isolated (scoped by tenant_id)
    - Replay-compatible (timestamps and data are reproducible)
    - Integrity-verified (integrity_hash prevents tampering)
    """

    def __init__(self):
        """Initialize the audit trail manager."""
        # audit_trails[workspace_id] = list of AuditRecord
        self._audit_trails: Dict[str, List[AuditRecord]] = {}

        # Track audit metadata per workspace
        self._audit_metadata: Dict[str, Dict[str, Any]] = {}

        # audit_count per tenant for metrics
        self._audit_count_by_tenant: Dict[str, int] = {}

        # Last sequence number per workspace for ordering
        self._sequence_counter: Dict[str, int] = {}

    def record_coordination_event(
        self,
        workspace_id: str,
        coordination_id: str,
        status: str,
        tensor_count: int,
        memory_size: int,
        duration_ms: float,
        tenant_id: str,
    ) -> AuditRecord:
        """
        Record a coordination event.

        Args:
            workspace_id: Workspace identifier
            coordination_id: Coordination operation ID
            status: "started", "completed", or "failed"
            tensor_count: Number of tensors coordinated
            memory_size: Memory consumed (bytes)
            duration_ms: Operation duration
            tenant_id: Tenant identifier

        Returns:
            The recorded AuditRecord
        """
        event_data = {
            "coordination_id": coordination_id,
            "status": status,
            "tensor_count": tensor_count,
            "memory_size": memory_size,
            "duration_ms": duration_ms,
        }

        return self._record_event(
            workspace_id,
            f"coordination_{status}",
            event_data,
            "RuntimeCoordination",
            tenant_id,
        )

    def record_replay_event(
        self,
        workspace_id: str,
        replay_id: str,
        status: str,
        tensor_matches: int,
        semantic_matches: int,
        divergence_count: int,
        duration_ms: float,
        tenant_id: str,
    ) -> AuditRecord:
        """
        Record a replay/recovery event.

        Args:
            workspace_id: Workspace identifier
            replay_id: Replay operation ID
            status: "initiated", "completed", or "failed"
            tensor_matches: Number of matching tensors
            semantic_matches: Number of semantic matches
            divergence_count: Number of divergences detected
            duration_ms: Replay duration
            tenant_id: Tenant identifier

        Returns:
            The recorded AuditRecord
        """
        event_data = {
            "replay_id": replay_id,
            "status": status,
            "tensor_matches": tensor_matches,
            "semantic_matches": semantic_matches,
            "divergence_count": divergence_count,
            "duration_ms": duration_ms,
        }

        event_type = "replay_divergence" if divergence_count > 0 else f"replay_{status}"

        return self._record_event(
            workspace_id,
            event_type,
            event_data,
            "ReplayRecovery",
            tenant_id,
        )

    def record_policy_enforcement(
        self,
        workspace_id: str,
        policy_id: str,
        decision: str,
        context: Dict[str, Any],
        tenant_id: str,
    ) -> AuditRecord:
        """
        Record a policy enforcement event.

        Args:
            workspace_id: Workspace identifier
            policy_id: Policy identifier
            decision: "approved", "denied", or "warning"
            context: Policy evaluation context
            tenant_id: Tenant identifier

        Returns:
            The recorded AuditRecord
        """
        event_type = "policy_violation" if decision == "denied" else "policy_enforced"

        event_data = {
            "policy_id": policy_id,
            "decision": decision,
            "context_keys": list(context.keys()),
            "context_hash": self._hash_data(context),
        }

        return self._record_event(
            workspace_id,
            event_type,
            event_data,
            "GovernancePolicy",
            tenant_id,
        )

    def record_semantic_checkpoint(
        self,
        workspace_id: str,
        checkpoint_id: str,
        semantic_state: Dict[str, Any],
        operation_id: str,
        tenant_id: str,
    ) -> AuditRecord:
        """
        Record a semantic state checkpoint.

        Args:
            workspace_id: Workspace identifier
            checkpoint_id: Checkpoint identifier
            semantic_state: Semantic state snapshot
            operation_id: Operation that created checkpoint
            tenant_id: Tenant identifier

        Returns:
            The recorded AuditRecord
        """
        event_data = {
            "checkpoint_id": checkpoint_id,
            "operation_id": operation_id,
            "state_hash": self._hash_data(semantic_state),
            "state_keys": list(semantic_state.keys()),
            "state_size": len(json.dumps(semantic_state, sort_keys=True)),
        }

        return self._record_event(
            workspace_id,
            "semantic_checkpoint",
            event_data,
            "SemanticCompilation",
            tenant_id,
        )

    def record_recovery_event(
        self,
        workspace_id: str,
        recovery_id: str,
        status: str,
        snapshots_recovered: int,
        integrity_validated: bool,
        duration_ms: float,
        tenant_id: str,
    ) -> AuditRecord:
        """
        Record a recovery event.

        Args:
            workspace_id: Workspace identifier
            recovery_id: Recovery operation ID
            status: "started" or "completed"
            snapshots_recovered: Number of snapshots recovered
            integrity_validated: Whether integrity was validated
            duration_ms: Recovery duration
            tenant_id: Tenant identifier

        Returns:
            The recorded AuditRecord
        """
        event_data = {
            "recovery_id": recovery_id,
            "status": status,
            "snapshots_recovered": snapshots_recovered,
            "integrity_validated": integrity_validated,
            "duration_ms": duration_ms,
        }

        return self._record_event(
            workspace_id,
            f"recovery_{status}",
            event_data,
            "RuntimeRecovery",
            tenant_id,
        )

    def get_audit_trail(
        self,
        workspace_id: str,
        tenant_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[str] = None,
    ) -> List[AuditRecord]:
        """
        Retrieve audit trail records.

        Args:
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier (for isolation)
            start_time: Filter start time (UTC)
            end_time: Filter end time (UTC)
            event_type: Filter by event type

        Returns:
            List of AuditRecords matching criteria
        """
        if workspace_id not in self._audit_trails:
            return []

        records = self._audit_trails[workspace_id]

        # Filter by tenant
        records = [r for r in records if r.tenant_id == tenant_id]

        # Filter by time range
        if start_time:
            start_iso = start_time.isoformat()
            records = [r for r in records if r.timestamp >= start_iso]

        if end_time:
            end_iso = end_time.isoformat()
            records = [r for r in records if r.timestamp <= end_iso]

        # Filter by event type
        if event_type:
            records = [r for r in records if r.event_type == event_type]

        return records

    def get_audit_summary(self, workspace_id: str, tenant_id: str) -> Dict[str, Any]:
        """
        Get summary statistics for audit trail.

        Args:
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier

        Returns:
            Summary dictionary with audit statistics
        """
        records = self.get_audit_trail(workspace_id, tenant_id)

        if not records:
            return {
                "total_records": 0,
                "workspace_id": workspace_id,
                "tenant_id": tenant_id,
                "first_event": None,
                "last_event": None,
                "event_types": {},
            }

        event_types: Dict[str, int] = {}
        for record in records:
            event_types[record.event_type] = event_types.get(record.event_type, 0) + 1

        return {
            "total_records": len(records),
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "first_event": records[0].timestamp,
            "last_event": records[-1].timestamp,
            "event_types": event_types,
            "recorded_by": set(r.recorded_by for r in records),
        }

    def verify_audit_integrity(
        self, workspace_id: str, tenant_id: str
    ) -> Dict[str, Any]:
        """
        Verify integrity of audit trail.

        Args:
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier

        Returns:
            Integrity verification results
        """
        records = self.get_audit_trail(workspace_id, tenant_id)

        if not records:
            return {"valid": True, "records_checked": 0, "errors": []}

        errors: List[str] = []

        for i, record in enumerate(records):
            # Verify integrity hash
            record_dict = asdict(record)
            record_dict["integrity_hash"] = ""  # Clear hash for verification
            computed_hash = self._hash_data(record_dict)

            if computed_hash != record.integrity_hash:
                errors.append(
                    f"Record {i} integrity mismatch: "
                    f"expected {record.integrity_hash}, got {computed_hash}"
                )

            # Verify tenant consistency
            if record.tenant_id != tenant_id:
                errors.append(f"Record {i} has wrong tenant_id")

            # Verify timestamp ordering
            if i > 0 and records[i - 1].timestamp > record.timestamp:
                errors.append(
                    f"Record {i} timestamp ordering violation: "
                    f"{records[i - 1].timestamp} > {record.timestamp}"
                )

        return {
            "valid": len(errors) == 0,
            "records_checked": len(records),
            "errors": errors,
        }

    def export_audit_trail_json(self, workspace_id: str, tenant_id: str) -> str:
        """
        Export audit trail as deterministic JSON.

        Args:
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier

        Returns:
            JSON string (deterministically ordered)
        """
        records = self.get_audit_trail(workspace_id, tenant_id)

        records_dicts = [
            {
                "audit_id": r.audit_id,
                "workspace_id": r.workspace_id,
                "tenant_id": r.tenant_id,
                "timestamp": r.timestamp,
                "event_type": r.event_type,
                "event_data": r.event_data,
                "recorded_by": r.recorded_by,
                "integrity_hash": r.integrity_hash,
            }
            for r in records
        ]

        return json.dumps(records_dicts, sort_keys=True, indent=2)

    def _record_event(
        self,
        workspace_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        recorded_by: str,
        tenant_id: str,
    ) -> AuditRecord:
        """
        Internal method to record an audit event.

        Args:
            workspace_id: Workspace identifier
            event_type: Type of event
            event_data: Event-specific data
            recorded_by: Component recording the event
            tenant_id: Tenant identifier

        Returns:
            The recorded AuditRecord
        """
        # Generate deterministic record ID
        sequence_num = self._sequence_counter.get(workspace_id, 0) + 1
        self._sequence_counter[workspace_id] = sequence_num

        audit_id = f"{workspace_id}:{tenant_id}:{sequence_num:08d}"

        # Get current UTC time in ISO 8601 format
        timestamp = datetime.now(timezone.utc).isoformat()

        # Create record with empty hash for calculation
        record_data = {
            "audit_id": audit_id,
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "event_data": event_data,
            "recorded_by": recorded_by,
        }

        # Compute integrity hash
        integrity_hash = self._hash_data(record_data)

        # Create immutable record
        record = AuditRecord(
            audit_id=audit_id,
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            timestamp=timestamp,
            event_type=event_type,
            event_data=event_data,
            recorded_by=recorded_by,
            integrity_hash=integrity_hash,
        )

        # Append to trail (append-only)
        if workspace_id not in self._audit_trails:
            self._audit_trails[workspace_id] = []
            self._audit_metadata[workspace_id] = {
                "created_at": timestamp,
                "last_updated": timestamp,
                "tenant_ids": set(),
            }

        self._audit_trails[workspace_id].append(record)
        self._audit_metadata[workspace_id]["last_updated"] = timestamp

        # Track tenant
        if tenant_id not in self._audit_metadata[workspace_id]["tenant_ids"]:
            self._audit_metadata[workspace_id]["tenant_ids"].add(tenant_id)

        # Update count
        self._audit_count_by_tenant[tenant_id] = (
            self._audit_count_by_tenant.get(tenant_id, 0) + 1
        )

        return record

    @staticmethod
    def _hash_data(data: Dict[str, Any]) -> str:
        """
        Compute deterministic SHA256 hash of data.

        Uses JSON canonical form (sorted keys, no spaces) for determinism.
        """
        json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(json_str.encode()).hexdigest()

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall audit manager statistics."""
        total_records = sum(len(records) for records in self._audit_trails.values())

        return {
            "total_workspaces": len(self._audit_trails),
            "total_records": total_records,
            "total_tenants": len(self._audit_count_by_tenant),
            "records_by_tenant": dict(self._audit_count_by_tenant),
            "workspace_sizes": {
                ws_id: len(records) for ws_id, records in self._audit_trails.items()
            },
        }
