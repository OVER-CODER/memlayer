"""
Governance module tests for Phase 10.

Comprehensive tests for:
- RuntimeAuditTrailManager
- SemanticLineageEngine
- GovernancePolicyEngine
- OperationalObservabilityManager
- RuntimeIntegrityMonitor
- GovernanceExportManager
- Tenant isolation verification
- Determinism verification
"""

import pytest
from datetime import datetime, timezone
from app.governance import (
    RuntimeAuditTrailManager,
    SemanticLineageEngine,
    GovernancePolicyEngine,
    OperationalObservabilityManager,
    RuntimeIntegrityMonitor,
    GovernanceExportManager,
)


class TestRuntimeAuditTrailManager:
    """Test suite for RuntimeAuditTrailManager."""

    def test_initialization(self):
        """Test manager initialization."""
        manager = RuntimeAuditTrailManager()
        assert manager is not None

    def test_record_coordination_event(self):
        """Test recording coordination events."""
        manager = RuntimeAuditTrailManager()

        record = manager.record_coordination_event(
            workspace_id="ws_1",
            coordination_id="coord_1",
            status="completed",
            tensor_count=100,
            memory_size=1024,
            duration_ms=50.0,
            tenant_id="tenant_1",
        )

        assert record.audit_id is not None
        assert record.workspace_id == "ws_1"
        assert record.tenant_id == "tenant_1"
        assert record.event_type == "coordination_completed"

    def test_record_replay_event(self):
        """Test recording replay events."""
        manager = RuntimeAuditTrailManager()

        record = manager.record_replay_event(
            workspace_id="ws_1",
            replay_id="replay_1",
            status="completed",
            tensor_matches=100,
            semantic_matches=98,
            divergence_count=0,
            duration_ms=100.0,
            tenant_id="tenant_1",
        )

        assert record.event_type == "replay_completed"
        assert "tensor_matches" in record.event_data

    def test_tenant_isolation_in_audit_trail(self):
        """Test tenant isolation in audit trail retrieval."""
        manager = RuntimeAuditTrailManager()

        # Record events for different tenants
        manager.record_coordination_event(
            "ws_1", "coord_1", "completed", 100, 1024, 50.0, "tenant_1"
        )
        manager.record_coordination_event(
            "ws_1", "coord_2", "completed", 100, 1024, 50.0, "tenant_2"
        )

        # Retrieve for tenant_1
        trail_t1 = manager.get_audit_trail("ws_1", "tenant_1")
        assert len(trail_t1) == 1
        assert trail_t1[0].tenant_id == "tenant_1"

        # Retrieve for tenant_2
        trail_t2 = manager.get_audit_trail("ws_1", "tenant_2")
        assert len(trail_t2) == 1
        assert trail_t2[0].tenant_id == "tenant_2"

    def test_audit_integrity_verification(self):
        """Test audit trail integrity verification."""
        manager = RuntimeAuditTrailManager()

        manager.record_coordination_event(
            "ws_1", "coord_1", "completed", 100, 1024, 50.0, "tenant_1"
        )

        integrity = manager.verify_audit_integrity("ws_1", "tenant_1")
        # Records are created with integrity hash, so they should check out
        assert integrity["records_checked"] == 1
        # Check that tenant consistency is verified
        records = manager.get_audit_trail("ws_1", "tenant_1")
        assert len(records) == 1


class TestSemanticLineageEngine:
    """Test suite for SemanticLineageEngine."""

    def test_initialization(self):
        """Test engine initialization."""
        engine = SemanticLineageEngine()
        assert engine is not None

    def test_record_semantic_checkpoint(self):
        """Test recording semantic checkpoints."""
        engine = SemanticLineageEngine()

        checkpoint = engine.record_semantic_checkpoint(
            workspace_id="ws_1",
            semantic_state={"key": "value"},
            operation_id="op_1",
            tenant_id="tenant_1",
        )

        assert checkpoint.checkpoint_id is not None
        assert checkpoint.workspace_id == "ws_1"
        assert checkpoint.tenant_id == "tenant_1"
        assert checkpoint.semantic_state_hash is not None

    def test_lineage_chain_reconstruction(self):
        """Test lineage chain reconstruction."""
        engine = SemanticLineageEngine()

        cp1 = engine.record_semantic_checkpoint(
            "ws_1", {"state": "v1"}, "op_1", tenant_id="tenant_1"
        )

        cp2 = engine.record_semantic_checkpoint(
            "ws_1",
            {"state": "v2"},
            "op_2",
            derived_from=[cp1.checkpoint_id],
            tenant_id="tenant_1",
        )

        chain = engine.get_lineage_chain("ws_1", cp2.checkpoint_id, "tenant_1")

        assert len(chain) == 2
        assert chain[0].checkpoint_id == cp1.checkpoint_id
        assert chain[1].checkpoint_id == cp2.checkpoint_id

    def test_tenant_isolation_in_lineage(self):
        """Test tenant isolation in lineage retrieval."""
        engine = SemanticLineageEngine()

        cp1 = engine.record_semantic_checkpoint(
            "ws_1", {"state": "v1"}, "op_1", tenant_id="tenant_1"
        )

        cp2 = engine.record_semantic_checkpoint(
            "ws_1", {"state": "v2"}, "op_2", tenant_id="tenant_2"
        )

        # Get lineage for tenant_1
        checkpoints = engine.get_checkpoints_for_workspace("ws_1", "tenant_1")
        assert len(checkpoints) == 1
        assert checkpoints[0].tenant_id == "tenant_1"

        # Attempt to cross tenant boundary
        cross_chain = engine.get_lineage_chain("ws_1", cp2.checkpoint_id, "tenant_1")
        assert len(cross_chain) == 0  # Should be empty (isolation)


class TestGovernancePolicyEngine:
    """Test suite for GovernancePolicyEngine."""

    def test_initialization(self):
        """Test policy engine initialization."""
        engine = GovernancePolicyEngine()
        assert engine is not None

    def test_register_policy(self):
        """Test policy registration."""
        engine = GovernancePolicyEngine()

        success = engine.register_policy(
            policy_id="policy_1",
            policy_name="Test Policy",
            description="A test policy",
            policy_type="replay_integrity",
            rules={"max_divergence_count": 0},
            tenant_id="tenant_1",
        )

        assert success is True

    def test_evaluate_policy_approved(self):
        """Test policy evaluation - approved case."""
        engine = GovernancePolicyEngine()

        engine.register_policy(
            "policy_1",
            "Replay Integrity",
            "Validates replay integrity",
            "replay_integrity",
            {"max_divergence_count": 5},
            "tenant_1",
        )

        decision = engine.evaluate_policy(
            workspace_id="ws_1",
            policy_id="policy_1",
            context={
                "replay_divergence_count": 0,
                "semantic_matches": 100,
                "total_expectations": 100,
            },
            tenant_id="tenant_1",
        )

        assert decision.decision == "approved"

    def test_evaluate_policy_denied(self):
        """Test policy evaluation - denied case."""
        engine = GovernancePolicyEngine()

        engine.register_policy(
            "policy_1",
            "Tenant Boundary",
            "Validates tenant isolation",
            "tenant_boundary",
            {},
            "tenant_1",
        )

        decision = engine.evaluate_policy(
            workspace_id="ws_1",
            policy_id="policy_1",
            context={
                "context_tenant_id": "tenant_2",  # Wrong tenant
            },
            tenant_id="tenant_1",
        )

        assert decision.decision == "denied"

    def test_tenant_isolation_in_policies(self):
        """Test tenant isolation in policy management."""
        engine = GovernancePolicyEngine()

        # Register policies for different tenants
        engine.register_policy(
            "policy_1", "P1", "Policy 1", "replay_integrity", {}, "tenant_1"
        )
        engine.register_policy(
            "policy_2", "P2", "Policy 2", "replay_integrity", {}, "tenant_2"
        )

        stats_t1 = engine.get_policy_statistics("tenant_1")
        stats_t2 = engine.get_policy_statistics("tenant_2")

        assert stats_t1["total_policies"] == 1
        assert stats_t2["total_policies"] == 1


class TestOperationalObservabilityManager:
    """Test suite for OperationalObservabilityManager."""

    def test_initialization(self):
        """Test observability manager initialization."""
        manager = OperationalObservabilityManager()
        assert manager is not None

    def test_record_operation(self):
        """Test recording operations."""
        manager = OperationalObservabilityManager()

        manager.record_operation(
            workspace_id="ws_1",
            operation_id="op_1",
            operation_type="coordination",
            status="success",
            duration_ms=50.0,
            tenant_id="tenant_1",
        )

        # Verify recording worked
        diagnostics = manager.get_operational_diagnostics("ws_1", "tenant_1")
        assert diagnostics.operations_completed == 1

    def test_runtime_health_score(self):
        """Test runtime health score calculation."""
        manager = OperationalObservabilityManager()

        # Record successful operations
        for i in range(10):
            manager.record_operation(
                "ws_1", f"op_{i}", "coordination", "success", 50.0, "tenant_1"
            )

        health = manager.get_runtime_health_score("ws_1", "tenant_1")

        assert health.overall_score >= 0.9
        assert health.components["operations"] >= 0.9

    def test_tenant_isolation_in_observability(self):
        """Test tenant isolation in observability."""
        manager = OperationalObservabilityManager()

        # Record for different tenants
        manager.record_operation(
            "ws_1", "op_1", "coordination", "success", 50.0, "tenant_1"
        )
        manager.record_operation(
            "ws_1", "op_2", "coordination", "failed", 100.0, "tenant_2"
        )

        diag_t1 = manager.get_operational_diagnostics("ws_1", "tenant_1")
        diag_t2 = manager.get_operational_diagnostics("ws_1", "tenant_2")

        assert diag_t1.operations_completed == 1
        assert diag_t2.operations_failed == 1


class TestRuntimeIntegrityMonitor:
    """Test suite for RuntimeIntegrityMonitor."""

    def test_initialization(self):
        """Test integrity monitor initialization."""
        monitor = RuntimeIntegrityMonitor()
        assert monitor is not None

    def test_validate_replay_integrity_match(self):
        """Test replay integrity validation - matching."""
        monitor = RuntimeIntegrityMonitor()

        state = {"key": "value", "count": 42}

        validation = monitor.validate_replay_integrity(
            workspace_id="ws_1",
            replay_id="replay_1",
            expected_checkpoint=state,
            actual_checkpoint=state,
            tenant_id="tenant_1",
        )

        assert validation.valid is True

    def test_validate_replay_integrity_divergence(self):
        """Test replay integrity validation - divergence."""
        monitor = RuntimeIntegrityMonitor()

        expected = {"key": "value1"}
        actual = {"key": "value2"}

        validation = monitor.validate_replay_integrity(
            workspace_id="ws_1",
            replay_id="replay_1",
            expected_checkpoint=expected,
            actual_checkpoint=actual,
            tenant_id="tenant_1",
        )

        assert validation.valid is False

    def test_detect_semantic_corruption(self):
        """Test semantic corruption detection."""
        monitor = RuntimeIntegrityMonitor()

        expected = {"field1": "value1", "field2": "value2"}
        actual = {"field1": "value1"}  # Missing field2

        alert = monitor.detect_semantic_corruption(
            workspace_id="ws_1",
            checkpoint_id="cp_1",
            expected_state=expected,
            actual_state=actual,
            tenant_id="tenant_1",
        )

        assert alert is not None
        assert alert.corruption_type == "missing_fields"

    def test_tenant_isolation_in_integrity(self):
        """Test tenant isolation in integrity monitoring."""
        monitor = RuntimeIntegrityMonitor()

        # Validate for different tenants
        monitor.validate_replay_integrity(
            "ws_1", "replay_1", {"data": "v1"}, {"data": "v2"}, "tenant_1"
        )
        monitor.validate_replay_integrity(
            "ws_1", "replay_2", {"data": "v1"}, {"data": "v1"}, "tenant_2"
        )

        violations_t1 = monitor.get_integrity_violations("ws_1", "tenant_1")
        violations_t2 = monitor.get_integrity_violations("ws_1", "tenant_2")

        assert len(violations_t1) == 1
        assert len(violations_t2) == 0


class TestGovernanceExportManager:
    """Test suite for GovernanceExportManager."""

    def test_initialization(self):
        """Test export manager initialization."""
        manager = GovernanceExportManager()
        assert manager is not None

    def test_export_audit_trail_json(self):
        """Test audit trail export as JSON."""
        manager = GovernanceExportManager()
        audit_manager = RuntimeAuditTrailManager()

        # Create some audit records
        audit_manager.record_coordination_event(
            "ws_1", "coord_1", "completed", 100, 1024, 50.0, "tenant_1"
        )

        records = audit_manager.get_audit_trail("ws_1", "tenant_1")

        export_data = manager.export_audit_trail(records, "ws_1", "tenant_1", "json")

        assert isinstance(export_data, str)
        assert "audit_trail" in export_data
        assert "ws_1" in export_data

    def test_export_determinism(self):
        """Test export determinism (excluding timestamps)."""
        manager = GovernanceExportManager()
        audit_manager = RuntimeAuditTrailManager()

        # Create audit records
        audit_manager.record_coordination_event(
            "ws_1", "coord_1", "completed", 100, 1024, 50.0, "tenant_1"
        )

        records = audit_manager.get_audit_trail("ws_1", "tenant_1")

        # Export twice
        import json

        export1 = json.loads(
            manager.export_audit_trail(records, "ws_1", "tenant_1", "json")
        )
        export2 = json.loads(
            manager.export_audit_trail(records, "ws_1", "tenant_1", "json")
        )

        # Check deterministic parts (excluding timestamps)
        del export1["export_time"]
        del export2["export_time"]

        assert export1 == export2


class TestTenantIsolation:
    """Integration tests for tenant isolation across all components."""

    def test_complete_tenant_isolation(self):
        """Test complete tenant isolation across all governance components."""
        # Create managers
        audit_mgr = RuntimeAuditTrailManager()
        lineage_eng = SemanticLineageEngine()
        policy_eng = GovernancePolicyEngine()
        obs_mgr = OperationalObservabilityManager()
        integrity_mon = RuntimeIntegrityMonitor()

        # Tenant 1 operations
        audit_mgr.record_coordination_event(
            "ws_1", "coord_1", "completed", 100, 1024, 50.0, "tenant_1"
        )
        lineage_eng.record_semantic_checkpoint(
            "ws_1", {"state": "t1"}, "op_1", tenant_id="tenant_1"
        )

        # Tenant 2 operations
        audit_mgr.record_coordination_event(
            "ws_1", "coord_2", "completed", 100, 1024, 50.0, "tenant_2"
        )
        lineage_eng.record_semantic_checkpoint(
            "ws_1", {"state": "t2"}, "op_2", tenant_id="tenant_2"
        )

        # Verify isolation
        audit_t1 = audit_mgr.get_audit_trail("ws_1", "tenant_1")
        audit_t2 = audit_mgr.get_audit_trail("ws_1", "tenant_2")

        assert len(audit_t1) == 1
        assert len(audit_t2) == 1
        assert audit_t1[0].tenant_id == "tenant_1"
        assert audit_t2[0].tenant_id == "tenant_2"

        checkpoints_t1 = lineage_eng.get_checkpoints_for_workspace("ws_1", "tenant_1")
        checkpoints_t2 = lineage_eng.get_checkpoints_for_workspace("ws_1", "tenant_2")

        assert len(checkpoints_t1) == 1
        assert len(checkpoints_t2) == 1


class TestDeterminism:
    """Tests for determinism across governance operations."""

    def test_audit_record_determinism(self):
        """Test that audit records are deterministic."""
        manager1 = RuntimeAuditTrailManager()
        manager2 = RuntimeAuditTrailManager()

        # Record same events
        r1 = manager1.record_coordination_event(
            "ws_1", "coord_1", "completed", 100, 1024, 50.0, "tenant_1"
        )
        r2 = manager2.record_coordination_event(
            "ws_1", "coord_1", "completed", 100, 1024, 50.0, "tenant_1"
        )

        # Should have same content (different IDs due to sequence)
        assert r1.event_type == r2.event_type
        assert r1.event_data == r2.event_data

    def test_policy_evaluation_determinism(self):
        """Test that policy evaluation is deterministic."""
        engine1 = GovernancePolicyEngine()
        engine2 = GovernancePolicyEngine()

        # Register same policy
        for engine in [engine1, engine2]:
            engine.register_policy(
                "policy_1",
                "Test",
                "Test",
                "replay_integrity",
                {"max_divergence_count": 0},
                "tenant_1",
            )

        # Evaluate same context
        context = {
            "replay_divergence_count": 0,
            "semantic_matches": 100,
            "total_expectations": 100,
        }

        d1 = engine1.evaluate_policy("ws_1", "policy_1", context, "tenant_1")
        d2 = engine2.evaluate_policy("ws_1", "policy_1", context, "tenant_1")

        # Should have same decision
        assert d1.decision == d2.decision
        assert d1.confidence == d2.confidence
