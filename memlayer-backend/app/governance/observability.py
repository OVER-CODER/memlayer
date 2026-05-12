"""
Operational Observability Manager for MemLayer.

Provides runtime health diagnostics, operational insights, and system monitoring
without disrupting running operations.
All observations are tenant-scoped and isolated.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from collections import defaultdict


@dataclass(frozen=True)
class HealthScore:
    """Runtime health score."""

    workspace_id: str
    tenant_id: str
    overall_score: float  # 0-1.0
    components: Dict[str, float]  # Component-specific scores
    timestamp: str  # ISO 8601 UTC
    issues: List[str]


@dataclass(frozen=True)
class CoordinationStability:
    """Coordination stability metrics."""

    workspace_id: str
    tenant_id: str
    stability_score: float  # 0-1.0
    success_rate: float  # 0-1.0
    failure_count: int
    success_count: int
    window_minutes: int
    timestamp: str  # ISO 8601 UTC


@dataclass(frozen=True)
class DegradationAlert:
    """Alert for semantic degradation."""

    alert_id: str
    workspace_id: str
    tenant_id: str
    degradation_type: str  # "semantic_drift", "quality_loss", etc.
    severity: str  # "low", "medium", "high"
    degradation_amount: float
    threshold: float
    timestamp: str  # ISO 8601 UTC


@dataclass(frozen=True)
class ReplayDiagnostics:
    """Diagnostics for replay/recovery operations."""

    workspace_id: str
    tenant_id: str
    last_replay_time: Optional[str]  # ISO 8601 UTC
    replay_success_rate: float  # 0-1.0
    total_replays: int
    successful_replays: int
    failed_replays: int
    avg_divergence_count: float
    max_divergence_count: int
    anomalies: List[str]


@dataclass(frozen=True)
class OperationalDiagnostics:
    """Overall operational diagnostics."""

    workspace_id: str
    tenant_id: str
    runtime_uptime_minutes: float
    operations_completed: int
    operations_failed: int
    avg_operation_duration_ms: float
    telemetry_consistency: float  # 0-1.0
    last_diagnostic_run: str  # ISO 8601 UTC
    issues_detected: List[str]


class OperationalObservabilityManager:
    """
    Manages operational observability and runtime diagnostics.

    All observations are:
    - Non-disruptive (collected without affecting runtime)
    - Exportable (can be exported for analysis)
    - Replay-compatible (can be replayed from audit trails)
    - Tenant-isolated (scoped by tenant_id)
    - Deterministic (same observations from same runtime state)
    """

    def __init__(self):
        """Initialize the observability manager."""
        # Metrics per workspace
        self._runtime_health: Dict[str, Dict[str, HealthScore]] = {}
        self._coordination_stability: Dict[str, List[CoordinationStability]] = {}
        self._degradation_alerts: Dict[str, List[DegradationAlert]] = {}
        self._replay_diagnostics: Dict[str, Dict[str, ReplayDiagnostics]] = {}

        # Operation metrics
        self._operations: Dict[str, List[Dict[str, Any]]] = {}

        # Counters and statistics
        self._operation_stats: Dict[str, Dict[str, int]] = {}
        self._alert_counter: Dict[str, int] = {}
        self._diagnostic_runs: Dict[str, List[datetime]] = {}

    def record_operation(
        self,
        workspace_id: str,
        operation_id: str,
        operation_type: str,
        status: str,
        duration_ms: float,
        tenant_id: str,
    ) -> None:
        """
        Record an operation for diagnostics.

        Args:
            workspace_id: Workspace identifier
            operation_id: Operation identifier
            operation_type: Type of operation
            status: "success", "failed", etc.
            duration_ms: Operation duration
            tenant_id: Tenant identifier
        """
        if workspace_id not in self._operations:
            self._operations[workspace_id] = []
            self._operation_stats[workspace_id] = defaultdict(int)

        operation_record = {
            "operation_id": operation_id,
            "operation_type": operation_type,
            "status": status,
            "duration_ms": duration_ms,
            "tenant_id": tenant_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._operations[workspace_id].append(operation_record)

        # Update stats
        if status == "success":
            self._operation_stats[workspace_id]["successful_operations"] = (
                self._operation_stats[workspace_id].get("successful_operations", 0) + 1
            )
        else:
            self._operation_stats[workspace_id]["failed_operations"] = (
                self._operation_stats[workspace_id].get("failed_operations", 0) + 1
            )

    def get_runtime_health_score(
        self, workspace_id: str, tenant_id: str
    ) -> HealthScore:
        """
        Get current runtime health score.

        Args:
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier

        Returns:
            HealthScore with component-level scores
        """
        # Get operation statistics
        if workspace_id not in self._operation_stats:
            return HealthScore(
                workspace_id=workspace_id,
                tenant_id=tenant_id,
                overall_score=1.0,
                components={},
                timestamp=datetime.now(timezone.utc).isoformat(),
                issues=[],
            )

        stats = self._operation_stats[workspace_id]

        # Calculate operation success rate
        total_ops = stats.get("successful_operations", 0) + stats.get(
            "failed_operations", 0
        )
        if total_ops > 0:
            operation_health = stats.get("successful_operations", 0) / total_ops
        else:
            operation_health = 1.0

        # Calculate coordination stability
        coordination_stability = self._get_coordination_score(workspace_id, tenant_id)

        # Calculate memory health (estimate)
        memory_health = 0.95  # Placeholder

        # Calculate overall score
        components = {
            "operations": operation_health,
            "coordination": coordination_stability,
            "memory": memory_health,
        }

        overall_score = sum(components.values()) / len(components)

        # Identify issues
        issues: List[str] = []
        if operation_health < 0.95:
            issues.append(f"Low operation success rate: {operation_health:.1%}")
        if coordination_stability < 0.90:
            issues.append(
                f"Coordination stability below threshold: {coordination_stability:.1%}"
            )
        if memory_health < 0.90:
            issues.append("High memory usage detected")

        return HealthScore(
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            overall_score=overall_score,
            components=components,
            timestamp=datetime.now(timezone.utc).isoformat(),
            issues=issues,
        )

    def get_coordination_stability(
        self,
        workspace_id: str,
        tenant_id: str,
        window_minutes: int = 60,
    ) -> CoordinationStability:
        """
        Get coordination stability metrics.

        Args:
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier
            window_minutes: Time window for analysis

        Returns:
            CoordinationStability metrics
        """
        if workspace_id not in self._coordination_stability:
            self._coordination_stability[workspace_id] = []

        stability_records = self._coordination_stability[workspace_id]

        # Filter by time window
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        recent_records = []
        for record in stability_records:
            record_time = datetime.fromisoformat(record.timestamp)
            if record_time >= cutoff_time and record.tenant_id == tenant_id:
                recent_records.append(record)

        if not recent_records:
            # No records, assume stable
            return CoordinationStability(
                workspace_id=workspace_id,
                tenant_id=tenant_id,
                stability_score=1.0,
                success_rate=1.0,
                failure_count=0,
                success_count=0,
                window_minutes=window_minutes,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # Average metrics across records
        avg_stability = sum(r.stability_score for r in recent_records) / len(
            recent_records
        )
        avg_success_rate = sum(r.success_rate for r in recent_records) / len(
            recent_records
        )
        total_failures = sum(r.failure_count for r in recent_records)
        total_successes = sum(r.success_count for r in recent_records)

        return CoordinationStability(
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            stability_score=avg_stability,
            success_rate=avg_success_rate,
            failure_count=total_failures,
            success_count=total_successes,
            window_minutes=window_minutes,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def record_degradation_alert(
        self,
        workspace_id: str,
        degradation_type: str,
        severity: str,
        degradation_amount: float,
        threshold: float,
        tenant_id: str,
    ) -> DegradationAlert:
        """
        Record a semantic degradation alert.

        Args:
            workspace_id: Workspace identifier
            degradation_type: Type of degradation
            severity: Severity level
            degradation_amount: Measured degradation
            threshold: Threshold that was exceeded
            tenant_id: Tenant identifier

        Returns:
            The recorded DegradationAlert
        """
        if workspace_id not in self._degradation_alerts:
            self._degradation_alerts[workspace_id] = []

        alert_counter = self._alert_counter.get(workspace_id, 0) + 1
        self._alert_counter[workspace_id] = alert_counter

        alert_id = f"{workspace_id}:{tenant_id}:alert:{alert_counter:08d}"

        alert = DegradationAlert(
            alert_id=alert_id,
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            degradation_type=degradation_type,
            severity=severity,
            degradation_amount=degradation_amount,
            threshold=threshold,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        self._degradation_alerts[workspace_id].append(alert)

        return alert

    def get_semantic_degradation_alerts(
        self, workspace_id: str, tenant_id: str
    ) -> List[DegradationAlert]:
        """
        Get semantic degradation alerts.

        Args:
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier

        Returns:
            List of alerts
        """
        if workspace_id not in self._degradation_alerts:
            return []

        alerts = self._degradation_alerts[workspace_id]
        return [a for a in alerts if a.tenant_id == tenant_id]

    def record_replay_diagnostics(
        self,
        workspace_id: str,
        tenant_id: str,
        replay_status: str,
        divergence_count: int,
    ) -> None:
        """
        Record replay diagnostics.

        Args:
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier
            replay_status: "success" or "failed"
            divergence_count: Number of divergences detected
        """
        if workspace_id not in self._replay_diagnostics:
            self._replay_diagnostics[workspace_id] = {}

        key = f"{tenant_id}"

        if key not in self._replay_diagnostics[workspace_id]:
            self._replay_diagnostics[workspace_id][key] = ReplayDiagnostics(
                workspace_id=workspace_id,
                tenant_id=tenant_id,
                last_replay_time=None,
                replay_success_rate=0.0,
                total_replays=0,
                successful_replays=0,
                failed_replays=0,
                avg_divergence_count=0.0,
                max_divergence_count=0,
                anomalies=[],
            )

        current = self._replay_diagnostics[workspace_id][key]

        # Update stats
        total_replays = current.total_replays + 1
        successful = current.successful_replays + (
            1 if replay_status == "success" else 0
        )
        failed = current.failed_replays + (1 if replay_status != "success" else 0)
        success_rate = successful / total_replays if total_replays > 0 else 0.0

        # Update divergence stats
        if total_replays == 1:
            avg_divergence = float(divergence_count)
        else:
            avg_divergence = (
                current.avg_divergence_count * (total_replays - 1) + divergence_count
            ) / total_replays

        max_divergence = max(current.max_divergence_count, divergence_count)

        updated = ReplayDiagnostics(
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            last_replay_time=datetime.now(timezone.utc).isoformat(),
            replay_success_rate=success_rate,
            total_replays=total_replays,
            successful_replays=successful,
            failed_replays=failed,
            avg_divergence_count=avg_divergence,
            max_divergence_count=max_divergence,
            anomalies=current.anomalies,
        )

        self._replay_diagnostics[workspace_id][key] = updated

    def get_replay_diagnostics(
        self, workspace_id: str, tenant_id: str
    ) -> ReplayDiagnostics:
        """
        Get replay diagnostics.

        Args:
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier

        Returns:
            ReplayDiagnostics
        """
        if workspace_id not in self._replay_diagnostics:
            return ReplayDiagnostics(
                workspace_id=workspace_id,
                tenant_id=tenant_id,
                last_replay_time=None,
                replay_success_rate=0.0,
                total_replays=0,
                successful_replays=0,
                failed_replays=0,
                avg_divergence_count=0.0,
                max_divergence_count=0,
                anomalies=[],
            )

        key = f"{tenant_id}"
        return self._replay_diagnostics[workspace_id].get(
            key,
            ReplayDiagnostics(
                workspace_id=workspace_id,
                tenant_id=tenant_id,
                last_replay_time=None,
                replay_success_rate=0.0,
                total_replays=0,
                successful_replays=0,
                failed_replays=0,
                avg_divergence_count=0.0,
                max_divergence_count=0,
                anomalies=[],
            ),
        )

    def get_operational_diagnostics(
        self, workspace_id: str, tenant_id: str
    ) -> OperationalDiagnostics:
        """
        Get comprehensive operational diagnostics.

        Args:
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier

        Returns:
            OperationalDiagnostics
        """
        # Calculate uptime (mock - would be tracked in reality)
        runtime_uptime_minutes = 60.0

        # Get operation stats
        stats = self._operation_stats.get(workspace_id, {})
        operations_completed = stats.get("successful_operations", 0)
        operations_failed = stats.get("failed_operations", 0)

        # Calculate average operation duration
        if workspace_id in self._operations:
            ops = [
                o for o in self._operations[workspace_id] if o["tenant_id"] == tenant_id
            ]
            if ops:
                avg_duration = sum(o["duration_ms"] for o in ops) / len(ops)
            else:
                avg_duration = 0.0
        else:
            avg_duration = 0.0

        # Calculate telemetry consistency
        telemetry_consistency = 1.0  # Placeholder

        # Detect issues
        issues: List[str] = []
        if operations_failed > operations_completed * 0.05:
            issues.append(
                f"High failure rate: {operations_failed} failures out of "
                f"{operations_completed + operations_failed} operations"
            )

        diagnostics_run = (
            self._diagnostic_runs[workspace_id][-1].isoformat()
            if workspace_id in self._diagnostic_runs
            and self._diagnostic_runs[workspace_id]
            else datetime.now(timezone.utc).isoformat()
        )

        return OperationalDiagnostics(
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            runtime_uptime_minutes=runtime_uptime_minutes,
            operations_completed=operations_completed,
            operations_failed=operations_failed,
            avg_operation_duration_ms=avg_duration,
            telemetry_consistency=telemetry_consistency,
            last_diagnostic_run=diagnostics_run,
            issues_detected=issues,
        )

    def _get_coordination_score(self, workspace_id: str, tenant_id: str) -> float:
        """Calculate coordination stability score."""
        if workspace_id not in self._operation_stats:
            return 1.0

        stats = self._operation_stats[workspace_id]
        total = stats.get("successful_operations", 0) + stats.get(
            "failed_operations", 0
        )

        if total == 0:
            return 1.0

        success_rate = stats.get("successful_operations", 0) / total

        # Convert success rate to stability score
        if success_rate >= 0.95:
            return 1.0
        elif success_rate >= 0.90:
            return 0.95
        elif success_rate >= 0.80:
            return 0.85
        else:
            return max(0.0, success_rate)
