"""Phase 9 — Deployment Infrastructure test suite.

Validates:
- DeploymentConfigurationManager: modes, validation, export
- WorkspacePersistenceManager: persist, load, integrity, filesystem
- TenantWorkspaceManager: isolation, access, limits, reporting
- WorkspaceSnapshotEngine: checkpoints, restore, comparison, rollback
- RuntimeSessionManager: lifecycle, checkpointing, pause/resume, metrics
- RuntimeRecoveryManager: checkpoint recovery, persistence fallback, integrity
- Cross-component integration and recovery determinism
"""

import json
import pytest

from app.deployment import (
    DeploymentConfigurationManager,
    DeploymentConfiguration,
    DeploymentMode,
    PersistenceConfig,
    RuntimeConfig,
    TenantConfig,
    WorkspacePersistenceManager,
    PersistedWorkspace,
    TenantWorkspaceManager,
    WorkspaceSnapshotEngine,
    RuntimeSessionManager,
    SessionStatus,
    RuntimeRecoveryManager,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _workspace(ws_id="ws-1", tenant="t-1", mem_count=5):
    return PersistedWorkspace(
        workspace_id=ws_id,
        tenant_id=tenant,
        memories=[{"id": f"m-{i}", "content": f"memory {i}"} for i in range(mem_count)],
        provider="claude",
        token_budget=4000,
    )


# ---------------------------------------------------------------------------
# DeploymentConfigurationManager
# ---------------------------------------------------------------------------

class TestDeploymentConfiguration:

    def test_local_config(self):
        mgr = DeploymentConfigurationManager.local()
        assert mgr.config.mode == DeploymentMode.LOCAL
        assert mgr.config.persistence.storage_dir == ".memlayer/data"

    def test_hosted_config(self):
        mgr = DeploymentConfigurationManager.hosted()
        assert mgr.config.mode == DeploymentMode.HOSTED
        assert mgr.config.persistence.compression is True

    def test_self_hosted_config(self):
        mgr = DeploymentConfigurationManager.self_hosted()
        assert mgr.config.mode == DeploymentMode.SELF_HOSTED
        assert mgr.config.runtime.replay_history_limit == 5000

    def test_validation(self):
        mgr = DeploymentConfigurationManager()
        result = mgr.validate()
        assert result["valid"] is True

    def test_export(self, tmp_path):
        mgr = DeploymentConfigurationManager.local()
        out = str(tmp_path / "config.json")
        mgr.export_config(out)
        data = json.loads(open(out).read())
        assert data["mode"] == "local"

    def test_serialization(self):
        mgr = DeploymentConfigurationManager()
        payload = json.dumps(mgr.config.to_dict())
        parsed = json.loads(payload)
        assert "persistence" in parsed
        assert "runtime" in parsed


# ---------------------------------------------------------------------------
# WorkspacePersistenceManager
# ---------------------------------------------------------------------------

class TestWorkspacePersistence:

    def test_persist_and_load(self):
        mgr = WorkspacePersistenceManager(PersistenceConfig(auto_persist=False))
        ws = _workspace()
        mgr.persist(ws)
        loaded = mgr.load("ws-1")
        assert loaded is not None
        assert loaded.workspace_id == "ws-1"

    def test_checksum_computed_on_persist(self):
        mgr = WorkspacePersistenceManager(PersistenceConfig(auto_persist=False))
        ws = _workspace()
        record = mgr.persist(ws)
        assert record["checksum"] != ""

    def test_integrity_valid(self):
        mgr = WorkspacePersistenceManager(PersistenceConfig(auto_persist=False))
        ws = _workspace()
        mgr.persist(ws)
        result = mgr.verify_integrity("ws-1")
        assert result["valid"] is True

    def test_delete(self):
        mgr = WorkspacePersistenceManager(PersistenceConfig(auto_persist=False))
        ws = _workspace()
        mgr.persist(ws)
        assert mgr.delete("ws-1") is True
        assert mgr.load("ws-1") is None

    def test_list_by_tenant(self):
        mgr = WorkspacePersistenceManager(PersistenceConfig(auto_persist=False))
        mgr.persist(_workspace("ws-a", "t-1"))
        mgr.persist(_workspace("ws-b", "t-1"))
        mgr.persist(_workspace("ws-c", "t-2"))
        assert len(mgr.list_workspaces("t-1")) == 2
        assert len(mgr.list_workspaces("t-2")) == 1

    def test_filesystem_persistence(self, tmp_path):
        cfg = PersistenceConfig(storage_dir=str(tmp_path), auto_persist=True)
        mgr = WorkspacePersistenceManager(cfg)
        ws = _workspace()
        mgr.persist(ws)

        # New manager should find it on disk
        mgr2 = WorkspacePersistenceManager(cfg)
        loaded = mgr2.load("ws-1")
        assert loaded is not None
        assert loaded.workspace_id == "ws-1"
        assert len(loaded.memories) == 5

    def test_persistence_metrics(self):
        mgr = WorkspacePersistenceManager(PersistenceConfig(auto_persist=False))
        mgr.persist(_workspace("ws-a"))
        mgr.persist(_workspace("ws-b"))
        metrics = mgr.get_persistence_metrics()
        assert metrics["total_workspaces"] == 2
        assert metrics["total_persist_operations"] == 2


# ---------------------------------------------------------------------------
# TenantWorkspaceManager
# ---------------------------------------------------------------------------

class TestTenantManager:

    def test_register_tenant(self):
        mgr = TenantWorkspaceManager()
        tenant = mgr.register_tenant("t-1", name="Acme")
        assert tenant.tenant_id == "t-1"

    def test_create_workspace_for_tenant(self):
        mgr = TenantWorkspaceManager()
        mgr.register_tenant("t-1")
        ws_id = mgr.create_workspace("t-1", "ws-1")
        assert ws_id == "ws-1"

    def test_validate_access(self):
        mgr = TenantWorkspaceManager()
        mgr.register_tenant("t-1")
        mgr.register_tenant("t-2")
        mgr.create_workspace("t-1", "ws-1")
        assert mgr.validate_access("t-1", "ws-1") is True
        assert mgr.validate_access("t-2", "ws-1") is False

    def test_workspace_limit(self):
        config = TenantConfig(max_workspaces_per_tenant=2)
        mgr = TenantWorkspaceManager(config=config)
        mgr.register_tenant("t-1")
        mgr.create_workspace("t-1", "ws-1")
        mgr.create_workspace("t-1", "ws-2")
        with pytest.raises(ValueError, match="limit"):
            mgr.create_workspace("t-1", "ws-3")

    def test_isolation_report(self):
        mgr = TenantWorkspaceManager()
        mgr.register_tenant("t-1")
        mgr.register_tenant("t-2")
        mgr.create_workspace("t-1", "ws-a")
        mgr.create_workspace("t-2", "ws-b")
        report = mgr.get_isolation_report()
        assert report["isolation_intact"] is True
        assert report["total_workspaces"] == 2

    def test_remove_workspace(self):
        mgr = TenantWorkspaceManager()
        mgr.register_tenant("t-1")
        mgr.create_workspace("t-1", "ws-1")
        assert mgr.remove_workspace("t-1", "ws-1") is True
        assert mgr.validate_access("t-1", "ws-1") is False

    def test_unregistered_tenant_raises(self):
        mgr = TenantWorkspaceManager()
        with pytest.raises(ValueError, match="not found"):
            mgr.create_workspace("unknown", "ws-1")


# ---------------------------------------------------------------------------
# WorkspaceSnapshotEngine
# ---------------------------------------------------------------------------

class TestSnapshotEngine:

    def test_create_checkpoint(self):
        engine = WorkspaceSnapshotEngine()
        ws = _workspace()
        cp = engine.create_checkpoint(ws)
        assert cp.checkpoint_id.startswith("cp-")
        assert cp.memory_count == 5

    def test_restore_from_checkpoint(self):
        engine = WorkspaceSnapshotEngine()
        ws = _workspace()
        cp = engine.create_checkpoint(ws)

        restored = engine.restore_from_checkpoint(cp.checkpoint_id)
        assert restored is not None
        assert restored.workspace_id == "ws-1"
        assert len(restored.memories) == 5

    def test_restore_preserves_checksum(self):
        engine = WorkspaceSnapshotEngine()
        ws = _workspace()
        ws.compute_checksum()
        original_checksum = ws.checksum

        cp = engine.create_checkpoint(ws)
        restored = engine.restore_from_checkpoint(cp.checkpoint_id)
        assert restored.checksum == original_checksum

    def test_compare_checkpoints(self):
        engine = WorkspaceSnapshotEngine()
        ws = _workspace()
        cp1 = engine.create_checkpoint(ws)

        ws.memories.append({"id": "m-new", "content": "new"})
        ws.version = 2
        cp2 = engine.create_checkpoint(ws)

        result = engine.compare_checkpoints(cp1.checkpoint_id, cp2.checkpoint_id)
        assert result is not None
        assert result.checksums_match is False
        assert result.version_delta == 1
        assert result.memory_count_delta == 1

    def test_snapshot_limit(self):
        config = PersistenceConfig(max_snapshots_per_workspace=3)
        engine = WorkspaceSnapshotEngine(config)
        ws = _workspace()
        for i in range(5):
            ws.version = i + 1
            engine.create_checkpoint(ws)

        cps = engine.get_checkpoints("ws-1")
        assert len(cps) == 3

    def test_snapshot_metrics(self):
        engine = WorkspaceSnapshotEngine()
        engine.create_checkpoint(_workspace("ws-a"))
        engine.create_checkpoint(_workspace("ws-b"))
        metrics = engine.get_snapshot_metrics()
        assert metrics["total_checkpoints"] == 2


# ---------------------------------------------------------------------------
# RuntimeSessionManager
# ---------------------------------------------------------------------------

class TestSessionManager:

    def test_create_session(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session("t-1", workspace_ids=["ws-1"])
        assert session.status == SessionStatus.ACTIVE
        assert "ws-1" in session.workspace_ids

    def test_record_activity(self):
        mgr = RuntimeSessionManager()
        session = mgr.create_session("t-1", session_id="s-1")
        mgr.record_activity("s-1", tokens_consumed=500, coordination=True)
        updated = mgr.get_session("s-1")
        assert updated.total_tokens_consumed == 500
        assert updated.coordination_count == 1

    def test_pause_and_resume(self):
        mgr = RuntimeSessionManager()
        mgr.create_session("t-1", session_id="s-1")
        assert mgr.pause_session("s-1") is True
        assert mgr.get_session("s-1").status == SessionStatus.PAUSED
        assert mgr.resume_session("s-1") is True
        assert mgr.get_session("s-1").status == SessionStatus.ACTIVE

    def test_terminate(self):
        mgr = RuntimeSessionManager()
        mgr.create_session("t-1", session_id="s-1")
        assert mgr.terminate_session("s-1") is True
        assert mgr.get_session("s-1").status == SessionStatus.TERMINATED

    def test_active_sessions_by_tenant(self):
        mgr = RuntimeSessionManager()
        mgr.create_session("t-1", session_id="s-1")
        mgr.create_session("t-2", session_id="s-2")
        mgr.create_session("t-1", session_id="s-3")
        assert len(mgr.get_active_sessions("t-1")) == 2
        assert len(mgr.get_active_sessions("t-2")) == 1

    def test_session_metrics(self):
        mgr = RuntimeSessionManager()
        mgr.create_session("t-1", session_id="s-1")
        mgr.record_activity("s-1", tokens_consumed=1000, coordination=True)
        metrics = mgr.get_session_metrics()
        assert metrics["total_sessions"] == 1
        assert metrics["total_tokens_consumed"] == 1000

    def test_checkpoint_tracking(self):
        mgr = RuntimeSessionManager()
        mgr.create_session("t-1", session_id="s-1")
        mgr.add_checkpoint("s-1", "cp-001")
        mgr.add_checkpoint("s-1", "cp-002")
        session = mgr.get_session("s-1")
        assert len(session.checkpoint_ids) == 2


# ---------------------------------------------------------------------------
# RuntimeRecoveryManager
# ---------------------------------------------------------------------------

class TestRecoveryManager:

    def test_recover_from_checkpoint(self):
        persistence = WorkspacePersistenceManager(PersistenceConfig(auto_persist=False))
        snapshots = WorkspaceSnapshotEngine()
        sessions = RuntimeSessionManager()

        # Setup: persist workspace, checkpoint, create session
        ws = _workspace("ws-1")
        persistence.persist(ws)
        snapshots.create_checkpoint(ws)
        sessions.create_session("t-1", session_id="s-1", workspace_ids=["ws-1"])

        # Recover
        recovery = RuntimeRecoveryManager(persistence, snapshots, sessions)
        results = recovery.recover_session("s-1")
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].integrity_valid is True

    def test_recover_from_persistence_fallback(self):
        persistence = WorkspacePersistenceManager(PersistenceConfig(auto_persist=False))
        snapshots = WorkspaceSnapshotEngine()  # No checkpoints
        sessions = RuntimeSessionManager()

        ws = _workspace("ws-1")
        persistence.persist(ws)
        sessions.create_session("t-1", session_id="s-1", workspace_ids=["ws-1"])

        recovery = RuntimeRecoveryManager(persistence, snapshots, sessions)
        results = recovery.recover_session("s-1")
        assert results[0].success is True
        assert results[0].recovered_from == "persistence"

    def test_recover_no_source(self):
        persistence = WorkspacePersistenceManager(PersistenceConfig(auto_persist=False))
        sessions = RuntimeSessionManager()
        sessions.create_session("t-1", session_id="s-1", workspace_ids=["ws-missing"])

        recovery = RuntimeRecoveryManager(persistence, sessions=sessions)
        results = recovery.recover_session("s-1")
        assert results[0].success is False
        assert results[0].recovered_from == "no_source"

    def test_session_resumed_after_recovery(self):
        persistence = WorkspacePersistenceManager(PersistenceConfig(auto_persist=False))
        snapshots = WorkspaceSnapshotEngine()
        sessions = RuntimeSessionManager()

        ws = _workspace("ws-1")
        persistence.persist(ws)
        snapshots.create_checkpoint(ws)
        sessions.create_session("t-1", session_id="s-1", workspace_ids=["ws-1"])

        recovery = RuntimeRecoveryManager(persistence, snapshots, sessions)
        recovery.recover_session("s-1")
        assert sessions.get_session("s-1").status == SessionStatus.ACTIVE

    def test_recovery_metrics(self):
        persistence = WorkspacePersistenceManager(PersistenceConfig(auto_persist=False))
        snapshots = WorkspaceSnapshotEngine()
        sessions = RuntimeSessionManager()

        ws = _workspace("ws-1")
        persistence.persist(ws)
        snapshots.create_checkpoint(ws)
        sessions.create_session("t-1", session_id="s-1", workspace_ids=["ws-1"])

        recovery = RuntimeRecoveryManager(persistence, snapshots, sessions)
        recovery.recover_session("s-1")
        metrics = recovery.get_recovery_metrics()
        assert metrics["total_recoveries"] == 1
        assert metrics["success_rate"] == 1.0


# ---------------------------------------------------------------------------
# Cross-component integration
# ---------------------------------------------------------------------------

class TestDeploymentIntegration:

    def test_full_deployment_lifecycle(self, tmp_path):
        """Config → tenant → workspace → persist → snapshot → recover."""
        # 1. Config
        cfg = DeploymentConfigurationManager.local(str(tmp_path / "data"))

        # 2. Tenancy
        tenants = TenantWorkspaceManager(config=cfg.config.tenant)
        tenants.register_tenant("acme", name="Acme Corp")
        ws_id = tenants.create_workspace("acme", "ws-acme-1")

        # 3. Persist
        persistence = WorkspacePersistenceManager(cfg.config.persistence)
        ws = PersistedWorkspace(
            workspace_id=ws_id, tenant_id="acme",
            memories=[{"id": f"m-{i}", "content": f"mem {i}"} for i in range(10)],
        )
        persistence.persist(ws)

        # 4. Snapshot
        snapshots = WorkspaceSnapshotEngine(cfg.config.persistence)
        cp = snapshots.create_checkpoint(ws)

        # 5. Simulate interruption + recovery
        sessions = RuntimeSessionManager(cfg.config.runtime.session_timeout_seconds)
        sessions.create_session("acme", session_id="s-acme", workspace_ids=[ws_id])

        recovery = RuntimeRecoveryManager(persistence, snapshots, sessions)
        results = recovery.recover_session("s-acme")
        assert results[0].success is True
        assert results[0].integrity_valid is True

        # 6. Verify isolation
        report = tenants.get_isolation_report()
        assert report["isolation_intact"] is True

    def test_multi_tenant_isolation(self):
        """Multiple tenants with isolated workspaces."""
        persistence = WorkspacePersistenceManager(PersistenceConfig(auto_persist=False))
        tenants = TenantWorkspaceManager(persistence)

        tenants.register_tenant("t-a")
        tenants.register_tenant("t-b")
        tenants.create_workspace("t-a", "ws-a1")
        tenants.create_workspace("t-a", "ws-a2")
        tenants.create_workspace("t-b", "ws-b1")

        assert tenants.validate_access("t-a", "ws-a1") is True
        assert tenants.validate_access("t-b", "ws-a1") is False
        assert tenants.validate_access("t-a", "ws-b1") is False

        report = tenants.get_isolation_report()
        assert report["isolation_intact"] is True
        assert report["total_workspaces"] == 3

    def test_deterministic_persistence(self):
        """Same workspace state produces identical checksums."""
        checksums = []
        for _ in range(3):
            mgr = WorkspacePersistenceManager(PersistenceConfig(auto_persist=False))
            ws = _workspace("ws-det", "t-1", 10)
            mgr.persist(ws)
            checksums.append(ws.checksum)
        assert len(set(checksums)) == 1
