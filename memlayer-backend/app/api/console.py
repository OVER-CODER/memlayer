"""
Console API for MemLayer Frontend Platform.
Exposes runtime SDK, Telemetry, and Governance layers.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.sdk import MemLayerSDK, WorkspaceConfig
from app.governance import (
    RuntimeAuditTrailManager,
    SemanticLineageEngine,
    GovernancePolicyEngine,
    OperationalObservabilityManager,
    RuntimeIntegrityMonitor
)
from app.agent_runtime.runtime_kernel import SharedAgentRuntime
from app.view_engine.compiler import ViewEngineCompiler, WorkspaceSemanticState
from app.runtime.integrated_runtime import IntegratedRuntimeSystem
from app.compiler.adaptive_assembly_pipeline import AdaptiveAssemblyPipeline

router = APIRouter(prefix="/api/console", tags=["console"])

# Global SDK and Governance Instances for the console
_pipeline = AdaptiveAssemblyPipeline()
_integrated_runtime = IntegratedRuntimeSystem(_pipeline)
sdk = MemLayerSDK(_integrated_runtime)

audit_manager = RuntimeAuditTrailManager()
lineage_engine = SemanticLineageEngine()
policy_engine = GovernancePolicyEngine(audit_manager)
observability_manager = OperationalObservabilityManager()
integrity_monitor = RuntimeIntegrityMonitor(audit_manager, lineage_engine)


@router.get("/workspaces")
def list_workspaces():
    return {"workspaces": sdk.workspaces.list_workspaces()}

@router.post("/workspaces")
def create_workspace(payload: Dict[str, Any]):
    ws_id = payload.get("workspace_id")
    provider = payload.get("provider", "claude")
    budget = payload.get("token_budget", 4000)
    snap = sdk.create_workspace(workspace_id=ws_id, provider=provider, token_budget=budget)
    return snap.to_dict()

@router.get("/workspaces/{workspace_id}/diagnostics")
def get_workspace_diagnostics(workspace_id: str):
    try:
        return sdk.workspaces.get_diagnostics(workspace_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/workspaces/{workspace_id}/coordinate")
def coordinate_workspace(workspace_id: str, payload: Dict[str, Any]):
    query = payload.get("query", "analyze workspace")
    try:
        res = sdk.coordinate(workspace_id, query)
        return res.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/telemetry")
def get_telemetry():
    return sdk.get_telemetry()

@router.get("/diagnostics")
def get_diagnostics():
    return sdk.get_diagnostics()

@router.get("/governance/audit-trail")
def get_audit_trail(tenant_id: str = "default", limit: int = 100):
    return [record.to_dict() for record in audit_manager.query_records(tenant_id=tenant_id, limit=limit)]

@router.get("/governance/health")
def get_governance_health(tenant_id: str = "default"):
    return observability_manager.get_health_report(tenant_id=tenant_id).to_dict()

@router.get("/governance/policy")
def get_policy_decisions(tenant_id: str = "default"):
    # Since policy engine holds decisions in memory or audit log,
    # we return a summary from the audit manager filtered by POLICY_ENFORCEMENT
    records = audit_manager.query_records(tenant_id=tenant_id, action_type="POLICY_ENFORCEMENT", limit=50)
    return [r.to_dict() for r in records]

@router.get("/governance/lineage")
def get_lineage(tenant_id: str = "default", workspace_id: Optional[str] = None):
    # For visualization, we need ancestry nodes
    if workspace_id:
        # Generate dummy data or fetch real lineage
        pass
    
    return {"nodes": [], "edges": []}

@router.post("/seed-mock-data")
def seed_mock_data():
    """Seeds the SDK with data for testing the frontend console."""
    ws1 = sdk.create_workspace(workspace_id="ws-research-1", provider="claude")
    sdk.add_memories(ws1.workspace_id, [{"id": f"m-{i}", "content": f"Memory {i}"} for i in range(10)])
    sdk.coordinate(ws1.workspace_id, "analyze market trends")
    
    ws2 = sdk.create_workspace(workspace_id="ws-finance-1", provider="openai")
    sdk.add_memories(ws2.workspace_id, [{"id": f"m-{i}", "content": f"Financial data {i}"} for i in range(50)])
    sdk.coordinate(ws2.workspace_id, "summarize Q4")
    
    # Generate some governance records
    audit_manager.record_event(
        tenant_id="default",
        action_type="WORKSPACE_CREATED",
        actor="system",
        resource_id=ws1.workspace_id,
        details={"provider": "claude"}
    )
    audit_manager.record_event(
        tenant_id="default",
        action_type="POLICY_ENFORCEMENT",
        actor="policy_engine",
        resource_id=ws1.workspace_id,
        details={"policy": "TokenBudgetLimit", "status": "passed"}
    )
    
    observability_manager.record_health_metric("default", "SharedAgentRuntime", 0.95, {"latency": 450})
    observability_manager.record_health_metric("default", "ViewEngineCompiler", 0.99, {"cache_hit_rate": 0.85})
    
    return {"status": "seeded"}
