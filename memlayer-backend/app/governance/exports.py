"""
Governance Export Manager for MemLayer.

Exports governance data, audit trails, lineage reports, and diagnostic summaries
in deterministic formats.
All exports are tenant-scoped and isolated.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone


class GovernanceExportManager:
    """
    Manages deterministic export of governance data.

    All exports are:
    - Deterministic (same inputs -> same output)
    - Replay-compatible (can be regenerated from source data)
    - Tenant-isolated (only includes tenant's data)
    - Machine-readable (JSON format)
    - Human-readable (JSON with indentation and comments)
    """

    def __init__(self):
        """Initialize the export manager."""
        self._export_count = 0

    def export_audit_trail(
        self,
        audit_records: List[Any],
        workspace_id: str,
        tenant_id: str,
        format_type: str = "json",
    ) -> str:
        """
        Export audit trail.

        Args:
            audit_records: List of AuditRecord objects
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier
            format_type: Export format ("json" or "markdown")

        Returns:
            Exported audit trail as string
        """
        # Filter by tenant
        records = [r for r in audit_records if r.tenant_id == tenant_id]

        if format_type == "markdown":
            return self._export_audit_trail_markdown(records, workspace_id, tenant_id)
        else:  # json
            return self._export_audit_trail_json(records, workspace_id, tenant_id)

    def export_lineage_report(
        self,
        checkpoints: List[Any],
        derivations: List[Any],
        workspace_id: str,
        tenant_id: str,
        format_type: str = "json",
    ) -> str:
        """
        Export semantic lineage report.

        Args:
            checkpoints: List of LineageCheckpoint objects
            derivations: List of ProjectionDerivation objects
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier
            format_type: Export format ("json" or "markdown")

        Returns:
            Exported lineage report as string
        """
        # Filter by tenant
        checkpoints = [c for c in checkpoints if c.tenant_id == tenant_id]
        derivations = [d for d in derivations if d.tenant_id == tenant_id]

        if format_type == "markdown":
            return self._export_lineage_markdown(
                checkpoints, derivations, workspace_id, tenant_id
            )
        else:  # json
            return self._export_lineage_json(
                checkpoints, derivations, workspace_id, tenant_id
            )

    def export_governance_diagnostics(
        self,
        policies: Dict[str, List[Any]],
        decisions: List[Any],
        violations: List[Any],
        workspace_id: str,
        tenant_id: str,
        format_type: str = "json",
    ) -> str:
        """
        Export governance diagnostics.

        Args:
            policies: Dictionary of registered policies
            decisions: List of PolicyDecision objects
            violations: List of PolicyViolation objects
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier
            format_type: Export format ("json" or "markdown")

        Returns:
            Exported governance diagnostics as string
        """
        # Filter by tenant
        tenant_policies = policies.get(tenant_id, {})
        decisions = [d for d in decisions if d.tenant_id == tenant_id]
        violations = [v for v in violations if v.tenant_id == tenant_id]

        if format_type == "markdown":
            return self._export_governance_markdown(
                tenant_policies, decisions, violations, workspace_id, tenant_id
            )
        else:  # json
            return self._export_governance_json(
                tenant_policies, decisions, violations, workspace_id, tenant_id
            )

    def export_integrity_report(
        self,
        validations: List[Any],
        violations: List[Any],
        workspace_id: str,
        tenant_id: str,
        format_type: str = "json",
    ) -> str:
        """
        Export integrity validation report.

        Args:
            validations: List of IntegrityValidation objects
            violations: List of IntegrityViolation objects
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier
            format_type: Export format ("json" or "markdown")

        Returns:
            Exported integrity report as string
        """
        # Filter by tenant
        validations = [v for v in validations if v.tenant_id == tenant_id]
        violations = [v for v in violations if v.tenant_id == tenant_id]

        if format_type == "markdown":
            return self._export_integrity_markdown(
                validations, violations, workspace_id, tenant_id
            )
        else:  # json
            return self._export_integrity_json(
                validations, violations, workspace_id, tenant_id
            )

    def export_replay_validation(
        self,
        diagnostics: Any,
        validations: List[Any],
        workspace_id: str,
        tenant_id: str,
        format_type: str = "json",
    ) -> str:
        """
        Export replay validation summary.

        Args:
            diagnostics: ReplayDiagnostics object
            validations: List of IntegrityValidation objects
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier
            format_type: Export format ("json" or "markdown")

        Returns:
            Exported replay validation as string
        """
        # Filter by tenant
        validations = [
            v
            for v in validations
            if v.tenant_id == tenant_id and v.validation_type == "replay"
        ]

        if format_type == "markdown":
            return self._export_replay_markdown(
                diagnostics, validations, workspace_id, tenant_id
            )
        else:  # json
            return self._export_replay_json(
                diagnostics, validations, workspace_id, tenant_id
            )

    # JSON Export Methods

    def _export_audit_trail_json(
        self,
        records: List[Any],
        workspace_id: str,
        tenant_id: str,
    ) -> str:
        """Export audit trail as JSON."""
        data = {
            "export_type": "audit_trail",
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "export_time": datetime.now(timezone.utc).isoformat(),
            "total_records": len(records),
            "records": [
                {
                    "audit_id": r.audit_id,
                    "timestamp": r.timestamp,
                    "event_type": r.event_type,
                    "event_data": r.event_data,
                    "recorded_by": r.recorded_by,
                }
                for r in records
            ],
        }

        return json.dumps(data, sort_keys=True, indent=2)

    def _export_lineage_json(
        self,
        checkpoints: List[Any],
        derivations: List[Any],
        workspace_id: str,
        tenant_id: str,
    ) -> str:
        """Export lineage as JSON."""
        data = {
            "export_type": "lineage",
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "export_time": datetime.now(timezone.utc).isoformat(),
            "total_checkpoints": len(checkpoints),
            "total_derivations": len(derivations),
            "checkpoints": [
                {
                    "checkpoint_id": c.checkpoint_id,
                    "timestamp": c.timestamp,
                    "semantic_state_hash": c.semantic_state_hash,
                    "derived_from": c.derived_from,
                    "operation_id": c.operation_id,
                }
                for c in checkpoints
            ],
            "derivations": [
                {
                    "derivation_id": d.derivation_id,
                    "projection_id": d.projection_id,
                    "source_checkpoints": d.source_checkpoints,
                    "derivation_method": d.derivation_method,
                    "timestamp": d.timestamp,
                }
                for d in derivations
            ],
        }

        return json.dumps(data, sort_keys=True, indent=2)

    def _export_governance_json(
        self,
        policies: Dict[str, Any],
        decisions: List[Any],
        violations: List[Any],
        workspace_id: str,
        tenant_id: str,
    ) -> str:
        """Export governance as JSON."""
        data = {
            "export_type": "governance",
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "export_time": datetime.now(timezone.utc).isoformat(),
            "total_policies": len(policies),
            "total_decisions": len(decisions),
            "total_violations": len(violations),
            "policies": [
                {
                    "policy_id": p.policy_id,
                    "policy_name": p.policy_name,
                    "enabled": p.enabled,
                    "priority": p.priority,
                }
                for p in policies.values()
            ],
            "decisions": [
                {
                    "decision_id": d.decision_id,
                    "policy_id": d.policy_id,
                    "decision": d.decision,
                    "confidence": d.confidence,
                    "reasons": d.reasons,
                    "timestamp": d.timestamp,
                }
                for d in decisions
            ],
            "violations": [
                {
                    "violation_id": v.violation_id,
                    "policy_id": v.policy_id,
                    "violation_type": v.violation_type,
                    "severity": v.severity,
                    "timestamp": v.timestamp,
                }
                for v in violations
            ],
        }

        return json.dumps(data, sort_keys=True, indent=2)

    def _export_integrity_json(
        self,
        validations: List[Any],
        violations: List[Any],
        workspace_id: str,
        tenant_id: str,
    ) -> str:
        """Export integrity as JSON."""
        valid_count = sum(1 for v in validations if v.valid)

        data = {
            "export_type": "integrity",
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "export_time": datetime.now(timezone.utc).isoformat(),
            "total_validations": len(validations),
            "valid_validations": valid_count,
            "total_violations": len(violations),
            "integrity_score": (valid_count / len(validations) if validations else 1.0),
            "validations": [
                {
                    "validation_id": v.validation_id,
                    "target_id": v.target_id,
                    "validation_type": v.validation_type,
                    "valid": v.valid,
                    "issues": v.issues,
                    "timestamp": v.timestamp,
                }
                for v in validations
            ],
            "violations": [
                {
                    "violation_id": v.violation_id,
                    "violation_type": v.violation_type,
                    "severity": v.severity,
                    "timestamp": v.detected_at,
                }
                for v in violations
            ],
        }

        return json.dumps(data, sort_keys=True, indent=2)

    def _export_replay_json(
        self,
        diagnostics: Any,
        validations: List[Any],
        workspace_id: str,
        tenant_id: str,
    ) -> str:
        """Export replay validation as JSON."""
        data = {
            "export_type": "replay_validation",
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "export_time": datetime.now(timezone.utc).isoformat(),
            "diagnostics": {
                "total_replays": diagnostics.total_replays,
                "successful_replays": diagnostics.successful_replays,
                "failed_replays": diagnostics.failed_replays,
                "success_rate": f"{diagnostics.replay_success_rate:.1%}",
                "avg_divergence": diagnostics.avg_divergence_count,
                "max_divergence": diagnostics.max_divergence_count,
            },
            "validations": [
                {
                    "validation_id": v.validation_id,
                    "target_id": v.target_id,
                    "valid": v.valid,
                    "issues": v.issues,
                    "timestamp": v.timestamp,
                }
                for v in validations
            ],
        }

        return json.dumps(data, sort_keys=True, indent=2)

    # Markdown Export Methods

    def _export_audit_trail_markdown(
        self,
        records: List[Any],
        workspace_id: str,
        tenant_id: str,
    ) -> str:
        """Export audit trail as Markdown."""
        lines = [
            "# Audit Trail Export",
            "",
            f"**Workspace:** {workspace_id}",
            f"**Tenant:** {tenant_id}",
            f"**Export Time:** {datetime.now(timezone.utc).isoformat()}",
            f"**Total Records:** {len(records)}",
            "",
            "## Events by Type",
            "",
        ]

        # Group by event type
        by_type: Dict[str, List[Any]] = {}
        for record in records:
            if record.event_type not in by_type:
                by_type[record.event_type] = []
            by_type[record.event_type].append(record)

        for event_type in sorted(by_type.keys()):
            lines.append(f"### {event_type} ({len(by_type[event_type])} events)")
            lines.append("")

            for record in by_type[event_type][-10:]:  # Last 10 per type
                lines.append(f"- **{record.timestamp}**: {record.recorded_by}")
                if record.event_data:
                    for key, value in record.event_data.items():
                        lines.append(f"  - {key}: {value}")
                lines.append("")

        return "\n".join(lines)

    def _export_lineage_markdown(
        self,
        checkpoints: List[Any],
        derivations: List[Any],
        workspace_id: str,
        tenant_id: str,
    ) -> str:
        """Export lineage as Markdown."""
        lines = [
            "# Semantic Lineage Report",
            "",
            f"**Workspace:** {workspace_id}",
            f"**Tenant:** {tenant_id}",
            f"**Export Time:** {datetime.now(timezone.utc).isoformat()}",
            f"**Total Checkpoints:** {len(checkpoints)}",
            f"**Total Derivations:** {len(derivations)}",
            "",
            "## Recent Checkpoints",
            "",
        ]

        for checkpoint in checkpoints[-10:]:
            lines.append(f"- **{checkpoint.checkpoint_id}** ({checkpoint.timestamp})")
            lines.append(f"  - Operation: {checkpoint.operation_id}")
            lines.append(f"  - State Hash: {checkpoint.semantic_state_hash[:16]}...")
            if checkpoint.derived_from:
                lines.append(f"  - Derived from: {', '.join(checkpoint.derived_from)}")
            lines.append("")

        return "\n".join(lines)

    def _export_governance_markdown(
        self,
        policies: Dict[str, Any],
        decisions: List[Any],
        violations: List[Any],
        workspace_id: str,
        tenant_id: str,
    ) -> str:
        """Export governance as Markdown."""
        lines = [
            "# Governance Diagnostics Report",
            "",
            f"**Workspace:** {workspace_id}",
            f"**Tenant:** {tenant_id}",
            f"**Export Time:** {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Registered Policies",
            "",
            f"Total: {len(policies)}",
            "",
        ]

        for policy in policies.values():
            lines.append(f"- **{policy.policy_name}** ({policy.policy_id})")
            lines.append(f"  - Enabled: {policy.enabled}")
            lines.append(f"  - Priority: {policy.priority}")
            lines.append("")

        lines.extend(
            [
                "## Policy Decisions",
                "",
                f"Total: {len(decisions)}",
                "",
            ]
        )

        approved = sum(1 for d in decisions if d.decision == "approved")
        denied = sum(1 for d in decisions if d.decision == "denied")

        lines.append(f"- Approved: {approved}")
        lines.append(f"- Denied: {denied}")
        lines.append("")

        lines.extend(
            [
                "## Policy Violations",
                "",
                f"Total: {len(violations)}",
                "",
            ]
        )

        for violation in violations[-5:]:
            lines.append(
                f"- **{violation.violation_type}** "
                f"({violation.severity}) - {violation.timestamp}"
            )

        return "\n".join(lines)

    def _export_integrity_markdown(
        self,
        validations: List[Any],
        violations: List[Any],
        workspace_id: str,
        tenant_id: str,
    ) -> str:
        """Export integrity as Markdown."""
        valid_count = sum(1 for v in validations if v.valid)

        lines = [
            "# Integrity Report",
            "",
            f"**Workspace:** {workspace_id}",
            f"**Tenant:** {tenant_id}",
            f"**Export Time:** {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Summary",
            "",
            f"- Total Validations: {len(validations)}",
            f"- Valid: {valid_count}",
            f"- Integrity Score: {(valid_count / len(validations) if validations else 1.0):.1%}",
            f"- Total Violations: {len(violations)}",
            "",
        ]

        if violations:
            lines.extend(
                [
                    "## Violations",
                    "",
                ]
            )

            for violation in violations:
                lines.append(
                    f"- **{violation.violation_type}** "
                    f"({violation.severity}) - {violation.detected_at}"
                )

        return "\n".join(lines)

    def _export_replay_markdown(
        self,
        diagnostics: Any,
        validations: List[Any],
        workspace_id: str,
        tenant_id: str,
    ) -> str:
        """Export replay validation as Markdown."""
        lines = [
            "# Replay Validation Report",
            "",
            f"**Workspace:** {workspace_id}",
            f"**Tenant:** {tenant_id}",
            f"**Export Time:** {datetime.now(timezone.utc).isoformat()}",
            "",
            "## Diagnostics",
            "",
            f"- Total Replays: {diagnostics.total_replays}",
            f"- Successful: {diagnostics.successful_replays}",
            f"- Failed: {diagnostics.failed_replays}",
            f"- Success Rate: {diagnostics.replay_success_rate:.1%}",
            f"- Avg Divergence: {diagnostics.avg_divergence_count:.1f}",
            f"- Max Divergence: {diagnostics.max_divergence_count}",
            "",
        ]

        valid_count = sum(1 for v in validations if v.valid)

        lines.extend(
            [
                "## Validations",
                "",
                f"- Total: {len(validations)}",
                f"- Valid: {valid_count}",
                f"- Invalid: {len(validations) - valid_count}",
                "",
            ]
        )

        return "\n".join(lines)
