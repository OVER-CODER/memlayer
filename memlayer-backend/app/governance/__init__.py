"""
Governance & Operational Observability module for MemLayer.

Provides enterprise runtime trust infrastructure including:
- Immutable audit trail recording
- Semantic lineage tracking
- Runtime governance policy enforcement
- Operational diagnostics and observability
- Runtime integrity monitoring
- Deterministic governance exports

All governance operations are:
- Tenant-isolated and scoped
- Deterministic and replayable
- Non-disruptive to runtime
- Focused on runtime trust, not enterprise CRUD
"""

from app.governance.audit_trail import (
    RuntimeAuditTrailManager,
    AuditRecord,
    AuditEventType,
)
from app.governance.lineage import (
    SemanticLineageEngine,
    LineageCheckpoint,
    ProjectionDerivation,
    SemanticAncestryGraph,
)
from app.governance.policy import (
    GovernancePolicyEngine,
    PolicyDefinition,
    PolicyDecision,
    PolicyViolation,
    PolicyDecisionType,
)
from app.governance.observability import (
    OperationalObservabilityManager,
    HealthScore,
    CoordinationStability,
    DegradationAlert,
    ReplayDiagnostics,
    OperationalDiagnostics,
)
from app.governance.integrity import (
    RuntimeIntegrityMonitor,
    CorruptionAlert,
    DivergenceAlert,
    IntegrityValidation,
    SnapshotValidation,
    IntegrityViolation,
)
from app.governance.exports import GovernanceExportManager

__all__ = [
    # Audit Trail
    "RuntimeAuditTrailManager",
    "AuditRecord",
    "AuditEventType",
    # Lineage
    "SemanticLineageEngine",
    "LineageCheckpoint",
    "ProjectionDerivation",
    "SemanticAncestryGraph",
    # Policy
    "GovernancePolicyEngine",
    "PolicyDefinition",
    "PolicyDecision",
    "PolicyViolation",
    "PolicyDecisionType",
    # Observability
    "OperationalObservabilityManager",
    "HealthScore",
    "CoordinationStability",
    "DegradationAlert",
    "ReplayDiagnostics",
    "OperationalDiagnostics",
    # Integrity
    "RuntimeIntegrityMonitor",
    "CorruptionAlert",
    "DivergenceAlert",
    "IntegrityValidation",
    "SnapshotValidation",
    "IntegrityViolation",
    # Exports
    "GovernanceExportManager",
]
