"""
Runtime Integrity Monitor for MemLayer.

Detects runtime corruption, semantic divergence, and persistence inconsistencies.
Validates snapshot integrity and coordination correctness.
All monitoring is tenant-scoped and isolated.
"""

import json
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class CorruptionAlert:
    """Alert for semantic corruption detected."""

    alert_id: str
    workspace_id: str
    tenant_id: str
    checkpoint_id: str
    corruption_type: str  # "state_mismatch", "hash_divergence", etc.
    expected_hash: str
    actual_hash: str
    details: Dict[str, Any]
    timestamp: str  # ISO 8601 UTC


@dataclass(frozen=True)
class DivergenceAlert:
    """Alert for persistence divergence detected."""

    alert_id: str
    workspace_id: str
    tenant_id: str
    snapshot_id: str
    divergence_type: str  # "data_mismatch", "missing_records", etc.
    magnitude: float  # 0-1.0
    details: Dict[str, Any]
    timestamp: str  # ISO 8601 UTC


@dataclass(frozen=True)
class IntegrityValidation:
    """Result of integrity validation."""

    validation_id: str
    workspace_id: str
    tenant_id: str
    target_id: str  # checkpoint, snapshot, or replay ID
    valid: bool
    validation_type: str  # "replay", "snapshot", "semantic", etc.
    issues: List[str]
    timestamp: str  # ISO 8601 UTC


@dataclass(frozen=True)
class SnapshotValidation:
    """Result of snapshot integrity validation."""

    validation_id: str
    workspace_id: str
    tenant_id: str
    snapshot_id: str
    valid: bool
    consistency_score: float  # 0-1.0
    data_integrity: bool
    metadata_integrity: bool
    issues: List[str]
    timestamp: str  # ISO 8601 UTC


@dataclass(frozen=True)
class IntegrityViolation:
    """Record of an integrity violation."""

    violation_id: str
    workspace_id: str
    tenant_id: str
    violation_type: str
    severity: str  # "low", "medium", "high", "critical"
    details: Dict[str, Any]
    detected_at: str  # ISO 8601 UTC


class RuntimeIntegrityMonitor:
    """
    Monitors runtime integrity and detects corruptions/divergences.

    All monitoring is:
    - Deterministic (same state -> same validation results)
    - Non-invasive (doesn't modify runtime)
    - Tenant-isolated (scoped by tenant_id)
    - Corruption-aware (detects multiple corruption types)
    - Recovery-aware (tracks what can be recovered)
    """

    def __init__(self):
        """Initialize the integrity monitor."""
        # Track validations
        self._validations: Dict[str, List[IntegrityValidation]] = {}

        # Track corruption alerts
        self._corruption_alerts: Dict[str, List[CorruptionAlert]] = {}

        # Track divergence alerts
        self._divergence_alerts: Dict[str, List[DivergenceAlert]] = {}

        # Track violations
        self._violations: Dict[str, List[IntegrityViolation]] = {}

        # Expected state registry (for validation)
        self._expected_states: Dict[str, Dict[str, Any]] = {}

        # Known good checksums
        self._known_checksums: Dict[str, str] = {}

        # Counters
        self._alert_counter: Dict[str, int] = {}
        self._validation_counter: Dict[str, int] = {}
        self._violation_counter: Dict[str, int] = {}

    def validate_replay_integrity(
        self,
        workspace_id: str,
        replay_id: str,
        expected_checkpoint: Dict[str, Any],
        actual_checkpoint: Dict[str, Any],
        tenant_id: str,
    ) -> IntegrityValidation:
        """
        Validate integrity of replay operation.

        Args:
            workspace_id: Workspace identifier
            replay_id: Replay operation ID
            expected_checkpoint: Expected final state
            actual_checkpoint: Actual final state
            tenant_id: Tenant identifier

        Returns:
            IntegrityValidation result
        """
        if workspace_id not in self._validations:
            self._validations[workspace_id] = []

        validation_counter = self._validation_counter.get(workspace_id, 0) + 1
        self._validation_counter[workspace_id] = validation_counter

        validation_id = f"{workspace_id}:{tenant_id}:val:{validation_counter:08d}"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Compute checksums
        expected_hash = self._compute_hash(expected_checkpoint)
        actual_hash = self._compute_hash(actual_checkpoint)

        valid = expected_hash == actual_hash
        issues: List[str] = []

        if not valid:
            issues.append(
                f"Replay produced different checkpoint: "
                f"expected {expected_hash[:16]}..., "
                f"got {actual_hash[:16]}..."
            )

            # Detect magnitude of difference
            diff_magnitude = self._estimate_magnitude(
                expected_checkpoint, actual_checkpoint
            )
            if diff_magnitude > 0.1:
                issues.append(f"Significant divergence detected: {diff_magnitude:.1%}")

        validation = IntegrityValidation(
            validation_id=validation_id,
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            target_id=replay_id,
            valid=valid,
            validation_type="replay",
            issues=issues,
            timestamp=timestamp,
        )

        self._validations[workspace_id].append(validation)

        # Record violation if not valid
        if not valid:
            self._record_violation(
                workspace_id,
                "replay_divergence",
                "high",
                {"replay_id": replay_id, "issues": issues},
                tenant_id,
            )

        return validation

    def detect_semantic_corruption(
        self,
        workspace_id: str,
        checkpoint_id: str,
        expected_state: Dict[str, Any],
        actual_state: Dict[str, Any],
        tenant_id: str,
    ) -> Optional[CorruptionAlert]:
        """
        Detect semantic state corruption.

        Args:
            workspace_id: Workspace identifier
            checkpoint_id: Checkpoint identifier
            expected_state: Expected semantic state
            actual_state: Actual semantic state
            tenant_id: Tenant identifier

        Returns:
            CorruptionAlert if corruption detected, None otherwise
        """
        expected_hash = self._compute_hash(expected_state)
        actual_hash = self._compute_hash(actual_state)

        if expected_hash == actual_hash:
            return None

        # Corruption detected
        if workspace_id not in self._corruption_alerts:
            self._corruption_alerts[workspace_id] = []

        alert_counter = self._alert_counter.get(workspace_id, 0) + 1
        self._alert_counter[workspace_id] = alert_counter

        alert_id = f"{workspace_id}:{tenant_id}:corr:{alert_counter:08d}"

        corruption_type = self._classify_corruption(expected_state, actual_state)

        alert = CorruptionAlert(
            alert_id=alert_id,
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            checkpoint_id=checkpoint_id,
            corruption_type=corruption_type,
            expected_hash=expected_hash,
            actual_hash=actual_hash,
            details={
                "expected_keys": list(expected_state.keys()),
                "actual_keys": list(actual_state.keys()),
                "missing_keys": list(
                    set(expected_state.keys()) - set(actual_state.keys())
                ),
                "extra_keys": list(
                    set(actual_state.keys()) - set(expected_state.keys())
                ),
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        self._corruption_alerts[workspace_id].append(alert)

        # Record violation
        self._record_violation(
            workspace_id,
            "semantic_corruption",
            "critical",
            {"checkpoint_id": checkpoint_id, "corruption_type": corruption_type},
            tenant_id,
        )

        return alert

    def detect_persistence_divergence(
        self,
        workspace_id: str,
        snapshot_id: str,
        persisted_data: Dict[str, Any],
        expected_data: Dict[str, Any],
        tenant_id: str,
    ) -> Optional[DivergenceAlert]:
        """
        Detect persistence divergence.

        Args:
            workspace_id: Workspace identifier
            snapshot_id: Snapshot identifier
            persisted_data: Data read from persistence
            expected_data: Expected data
            tenant_id: Tenant identifier

        Returns:
            DivergenceAlert if divergence detected, None otherwise
        """
        persisted_hash = self._compute_hash(persisted_data)
        expected_hash = self._compute_hash(expected_data)

        if persisted_hash == expected_hash:
            return None

        # Divergence detected
        if workspace_id not in self._divergence_alerts:
            self._divergence_alerts[workspace_id] = []

        alert_counter = self._alert_counter.get(workspace_id, 0) + 1
        self._alert_counter[workspace_id] = alert_counter

        alert_id = f"{workspace_id}:{tenant_id}:div:{alert_counter:08d}"

        magnitude = self._estimate_magnitude(expected_data, persisted_data)
        divergence_type = self._classify_divergence(expected_data, persisted_data)

        alert = DivergenceAlert(
            alert_id=alert_id,
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            snapshot_id=snapshot_id,
            divergence_type=divergence_type,
            magnitude=magnitude,
            details={
                "expected_hash": expected_hash[:16] + "...",
                "persisted_hash": persisted_hash[:16] + "...",
                "magnitude": magnitude,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        self._divergence_alerts[workspace_id].append(alert)

        # Record violation
        self._record_violation(
            workspace_id,
            "persistence_divergence",
            "high",
            {
                "snapshot_id": snapshot_id,
                "divergence_type": divergence_type,
                "magnitude": magnitude,
            },
            tenant_id,
        )

        return alert

    def validate_snapshot_integrity(
        self,
        workspace_id: str,
        snapshot_id: str,
        snapshot_data: Dict[str, Any],
        tenant_id: str,
    ) -> SnapshotValidation:
        """
        Validate snapshot integrity.

        Args:
            workspace_id: Workspace identifier
            snapshot_id: Snapshot identifier
            snapshot_data: Snapshot data to validate
            tenant_id: Tenant identifier

        Returns:
            SnapshotValidation result
        """
        if workspace_id not in self._validations:
            self._validations[workspace_id] = []

        validation_counter = self._validation_counter.get(workspace_id, 0) + 1
        self._validation_counter[workspace_id] = validation_counter

        validation_id = f"{workspace_id}:{tenant_id}:sval:{validation_counter:08d}"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Validate data structure
        data_integrity = self._validate_data_structure(snapshot_data)

        # Validate metadata
        metadata = snapshot_data.get("metadata", {})
        metadata_integrity = self._validate_metadata(metadata)

        # Calculate consistency score
        issues: List[str] = []

        if not data_integrity:
            issues.append("Data structure validation failed")

        if not metadata_integrity:
            issues.append("Metadata validation failed")

        consistency_score = 1.0 if (data_integrity and metadata_integrity) else 0.7

        valid = data_integrity and metadata_integrity

        validation = SnapshotValidation(
            validation_id=validation_id,
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            snapshot_id=snapshot_id,
            valid=valid,
            consistency_score=consistency_score,
            data_integrity=data_integrity,
            metadata_integrity=metadata_integrity,
            issues=issues,
            timestamp=timestamp,
        )

        self._validations[workspace_id].append(validation)

        if not valid:
            self._record_violation(
                workspace_id,
                "snapshot_integrity",
                "high",
                {"snapshot_id": snapshot_id, "issues": issues},
                tenant_id,
            )

        return validation

    def validate_coordination_integrity(
        self,
        workspace_id: str,
        coordination_id: str,
        tensor_count: int,
        semantic_count: int,
        tenant_id: str,
    ) -> IntegrityValidation:
        """
        Validate coordination integrity.

        Args:
            workspace_id: Workspace identifier
            coordination_id: Coordination operation ID
            tensor_count: Number of tensors coordinated
            semantic_count: Number of semantics coordinated
            tenant_id: Tenant identifier

        Returns:
            IntegrityValidation result
        """
        if workspace_id not in self._validations:
            self._validations[workspace_id] = []

        validation_counter = self._validation_counter.get(workspace_id, 0) + 1
        self._validation_counter[workspace_id] = validation_counter

        validation_id = f"{workspace_id}:{tenant_id}:cval:{validation_counter:08d}"
        timestamp = datetime.now(timezone.utc).isoformat()

        issues: List[str] = []
        valid = True

        # Check for coordination anomalies
        if tensor_count == 0 and semantic_count > 0:
            issues.append("Semantic coordination without tensors")
            valid = False

        if semantic_count == 0 and tensor_count > 0:
            issues.append("Tensor coordination without semantics")
            valid = False

        validation = IntegrityValidation(
            validation_id=validation_id,
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            target_id=coordination_id,
            valid=valid,
            validation_type="coordination",
            issues=issues,
            timestamp=timestamp,
        )

        self._validations[workspace_id].append(validation)

        if not valid:
            self._record_violation(
                workspace_id,
                "coordination_anomaly",
                "medium",
                {
                    "coordination_id": coordination_id,
                    "tensor_count": tensor_count,
                    "semantic_count": semantic_count,
                },
                tenant_id,
            )

        return validation

    def get_integrity_violations(
        self, workspace_id: str, tenant_id: str
    ) -> List[IntegrityViolation]:
        """
        Get integrity violations (tenant-scoped).

        Args:
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier

        Returns:
            List of violations
        """
        if workspace_id not in self._violations:
            return []

        violations = self._violations[workspace_id]
        return [v for v in violations if v.tenant_id == tenant_id]

    def get_integrity_summary(
        self, workspace_id: str, tenant_id: str
    ) -> Dict[str, Any]:
        """
        Get integrity summary.

        Args:
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier

        Returns:
            Summary dictionary
        """
        validations = [
            v
            for v in self._validations.get(workspace_id, [])
            if v.tenant_id == tenant_id
        ]
        corruptions = [
            a
            for a in self._corruption_alerts.get(workspace_id, [])
            if a.tenant_id == tenant_id
        ]
        divergences = [
            a
            for a in self._divergence_alerts.get(workspace_id, [])
            if a.tenant_id == tenant_id
        ]
        violations = self.get_integrity_violations(workspace_id, tenant_id)

        valid_count = sum(1 for v in validations if v.valid)

        return {
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "total_validations": len(validations),
            "valid_validations": valid_count,
            "corruption_alerts": len(corruptions),
            "divergence_alerts": len(divergences),
            "total_violations": len(violations),
            "integrity_score": (valid_count / len(validations) if validations else 1.0),
        }

    # Helper methods

    @staticmethod
    def _compute_hash(data: Dict[str, Any]) -> str:
        """Compute SHA256 hash of data."""
        json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(json_str.encode()).hexdigest()

    @staticmethod
    def _estimate_magnitude(expected: Dict[str, Any], actual: Dict[str, Any]) -> float:
        """Estimate magnitude of difference between two states."""
        total_keys = len(set(expected.keys()) | set(actual.keys()))
        if total_keys == 0:
            return 0.0

        different_keys = len(set(expected.keys()) ^ set(actual.keys())) + sum(
            1 for k in expected if k in actual and expected[k] != actual[k]
        )

        return different_keys / total_keys

    @staticmethod
    def _classify_corruption(expected: Dict[str, Any], actual: Dict[str, Any]) -> str:
        """Classify type of corruption."""
        missing = set(expected.keys()) - set(actual.keys())
        extra = set(actual.keys()) - set(expected.keys())

        if missing and not extra:
            return "missing_fields"
        elif extra and not missing:
            return "extra_fields"
        elif missing and extra:
            return "field_replacement"
        else:
            return "value_mismatch"

    @staticmethod
    def _classify_divergence(expected: Dict[str, Any], actual: Dict[str, Any]) -> str:
        """Classify type of divergence."""
        if len(actual) < len(expected):
            return "missing_records"
        elif len(actual) > len(expected):
            return "extra_records"
        else:
            return "data_mismatch"

    @staticmethod
    def _validate_data_structure(data: Dict[str, Any]) -> bool:
        """Validate snapshot data structure."""
        required_fields = ["id", "timestamp", "data"]
        return all(field in data for field in required_fields)

    @staticmethod
    def _validate_metadata(metadata: Dict[str, Any]) -> bool:
        """Validate snapshot metadata."""
        required_fields = ["version", "source"]
        return all(field in metadata for field in required_fields)

    def _record_violation(
        self,
        workspace_id: str,
        violation_type: str,
        severity: str,
        details: Dict[str, Any],
        tenant_id: str,
    ) -> None:
        """Record an integrity violation."""
        if workspace_id not in self._violations:
            self._violations[workspace_id] = []

        violation_counter = self._violation_counter.get(workspace_id, 0) + 1
        self._violation_counter[workspace_id] = violation_counter

        violation_id = f"{workspace_id}:{tenant_id}:viol:{violation_counter:08d}"

        violation = IntegrityViolation(
            violation_id=violation_id,
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            violation_type=violation_type,
            severity=severity,
            details=details,
            detected_at=datetime.now(timezone.utc).isoformat(),
        )

        self._violations[workspace_id].append(violation)
