"""Phase 9 — Deployment Infrastructure Benchmark Suite.

Measures:
1. Workspace persistence integrity
2. Replay recovery accuracy
3. Tenant isolation integrity
4. Snapshot restoration stability
5. Runtime session recovery
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.deployment import (
    WorkspacePersistenceManager,
    PersistedWorkspace,
    PersistenceConfig,
    TenantWorkspaceManager,
    TenantConfig,
    WorkspaceSnapshotEngine,
    RuntimeSessionManager,
    RuntimeRecoveryManager,
    DeploymentConfigurationManager,
)


def _workspace(ws_id, tenant="t-1", mem_count=20):
    return PersistedWorkspace(
        workspace_id=ws_id, tenant_id=tenant,
        memories=[{"id": f"m-{i}", "content": f"memory {i}"} for i in range(mem_count)],
        provider="claude", token_budget=4000,
    )


def benchmark_persistence_integrity(tmp_dir: str, cycles: int = 20):
    """Verify persisted workspaces restore with correct checksums."""
    cfg = PersistenceConfig(storage_dir=tmp_dir, auto_persist=True)
    results = []

    for i in range(cycles):
        mgr = WorkspacePersistenceManager(cfg)
        ws = _workspace(f"ws-pi-{i}", mem_count=10 + i * 5)
        mgr.persist(ws)

        # Reload from disk with fresh manager
        mgr2 = WorkspacePersistenceManager(cfg)
        loaded = mgr2.load(f"ws-pi-{i}")
        integrity = mgr2.verify_integrity(f"ws-pi-{i}")

        results.append({
            "cycle": i, "memory_count": 10 + i * 5,
            "integrity_valid": integrity["valid"],
            "checksum_match": integrity["stored_checksum"] == integrity["computed_checksum"],
        })

    all_valid = all(r["integrity_valid"] for r in results)
    return results, {"all_valid": all_valid, "cycles": cycles}


def benchmark_recovery_accuracy(cycles: int = 15):
    """Verify recovered runtimes preserve integrity."""
    results = []

    for i in range(cycles):
        persistence = WorkspacePersistenceManager(PersistenceConfig(auto_persist=False))
        snapshots = WorkspaceSnapshotEngine()
        sessions = RuntimeSessionManager()

        ws = _workspace(f"ws-rec-{i}", mem_count=10 + i)
        persistence.persist(ws)
        cp = snapshots.create_checkpoint(ws)
        sessions.create_session("t-1", session_id=f"s-{i}", workspace_ids=[f"ws-rec-{i}"])

        recovery = RuntimeRecoveryManager(persistence, snapshots, sessions)
        rec_results = recovery.recover_session(f"s-{i}")

        results.append({
            "cycle": i,
            "success": rec_results[0].success,
            "integrity_valid": rec_results[0].integrity_valid,
            "recovered_from": rec_results[0].recovered_from,
        })

    all_ok = all(r["success"] and r["integrity_valid"] for r in results)
    return results, {"all_recovered": all_ok, "cycles": cycles}


def benchmark_tenant_isolation(tenant_count: int = 10, ws_per_tenant: int = 5):
    """Verify tenant isolation at scale."""
    mgr = TenantWorkspaceManager()
    for t in range(tenant_count):
        mgr.register_tenant(f"tenant-{t}")
        for w in range(ws_per_tenant):
            mgr.create_workspace(f"tenant-{t}", f"tenant-{t}-ws-{w}")

    # Cross-tenant access checks
    violations = 0
    checks = 0
    for t in range(tenant_count):
        for other_t in range(tenant_count):
            if other_t == t:
                continue
            for w in range(ws_per_tenant):
                checks += 1
                if mgr.validate_access(f"tenant-{t}", f"tenant-{other_t}-ws-{w}"):
                    violations += 1

    report = mgr.get_isolation_report()
    return {
        "tenants": tenant_count,
        "workspaces_per_tenant": ws_per_tenant,
        "total_workspaces": report["total_workspaces"],
        "isolation_intact": report["isolation_intact"],
        "cross_tenant_checks": checks,
        "violations": violations,
    }


def benchmark_snapshot_restoration(cycles: int = 20):
    """Verify snapshot restoration preserves semantic continuity."""
    engine = WorkspaceSnapshotEngine()
    results = []

    for i in range(cycles):
        ws = _workspace(f"ws-snap", mem_count=10 + i)
        ws.version = i + 1
        cp = engine.create_checkpoint(ws)

        restored = engine.restore_from_checkpoint(cp.checkpoint_id)
        results.append({
            "cycle": i,
            "checksum_match": restored.checksum == cp.state_checksum,
            "memory_preserved": len(restored.memories) == 10 + i,
            "version": ws.version,
        })

    all_ok = all(r["checksum_match"] and r["memory_preserved"] for r in results)
    return results, {"all_restored": all_ok, "cycles": cycles}


def benchmark_session_recovery(cycles: int = 10):
    """Verify session recovery lifecycle."""
    results = []
    for i in range(cycles):
        persistence = WorkspacePersistenceManager(PersistenceConfig(auto_persist=False))
        snapshots = WorkspaceSnapshotEngine()
        sessions = RuntimeSessionManager()

        # Setup: 3 workspaces per session
        ws_ids = [f"ws-sess-{i}-{j}" for j in range(3)]
        for ws_id in ws_ids:
            ws = _workspace(ws_id, mem_count=5)
            persistence.persist(ws)
            snapshots.create_checkpoint(ws)

        sessions.create_session("t-1", session_id=f"sess-{i}", workspace_ids=ws_ids)

        # Recover
        recovery = RuntimeRecoveryManager(persistence, snapshots, sessions)
        rec_results = recovery.recover_session(f"sess-{i}")

        all_ok = all(r.success for r in rec_results)
        all_integrity = all(r.integrity_valid for r in rec_results)

        results.append({
            "cycle": i, "workspaces": len(ws_ids),
            "all_recovered": all_ok, "all_integrity": all_integrity,
        })

    return results, {
        "cycles": cycles,
        "all_sessions_recovered": all(r["all_recovered"] for r in results),
    }


def run_benchmark_campaign():
    import tempfile
    tmp = tempfile.mkdtemp()

    print("=" * 70)
    print("Phase 9 — Deployment Infrastructure Benchmark")
    print("=" * 70)

    print("\n[1/5] Persistence Integrity...")
    pi_rows, pi_summary = benchmark_persistence_integrity(os.path.join(tmp, "persist"))

    print("[2/5] Recovery Accuracy...")
    rec_rows, rec_summary = benchmark_recovery_accuracy()

    print("[3/5] Tenant Isolation...")
    iso_result = benchmark_tenant_isolation()

    print("[4/5] Snapshot Restoration...")
    snap_rows, snap_summary = benchmark_snapshot_restoration()

    print("[5/5] Session Recovery...")
    sess_rows, sess_summary = benchmark_session_recovery()

    summary = {
        "benchmark_run_at": datetime.now(timezone.utc).isoformat(),
        "persistence_integrity": pi_summary,
        "recovery_accuracy": rec_summary,
        "tenant_isolation": {
            "intact": iso_result["isolation_intact"],
            "violations": iso_result["violations"],
            "checks": iso_result["cross_tenant_checks"],
        },
        "snapshot_restoration": snap_summary,
        "session_recovery": sess_summary,
    }

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    for k, v in summary.items():
        if isinstance(v, dict):
            print(f"\n  {k}:")
            for kk, vv in v.items():
                print(f"    {kk}: {vv}")
        else:
            print(f"  {k}: {v}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(os.path.dirname(__file__), f"results_{timestamp}")
    os.makedirs(out_dir, exist_ok=True)

    for name, data in [
        ("summary", summary), ("persistence", pi_rows),
        ("recovery", rec_rows), ("isolation", iso_result),
        ("snapshots", snap_rows), ("sessions", sess_rows),
    ]:
        with open(os.path.join(out_dir, f"{name}.json"), "w") as f:
            json.dump(data, f, indent=2, default=str)

    print(f"\n  Results saved to: {out_dir}")
    return summary


if __name__ == "__main__":
    run_benchmark_campaign()
