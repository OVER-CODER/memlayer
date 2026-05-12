"""
Console API for MemLayer Frontend Platform.
Exposes runtime SDK, Telemetry, and Governance layers.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

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
from app.compiler.adaptive_compilation import RelevanceRankingService
from app.services.embedding import get_embedding_service

router = APIRouter(prefix="/api/console", tags=["console"])

# Global SDK and Governance Instances for the console
_embedding_service = get_embedding_service()
_ranking_service = RelevanceRankingService(_embedding_service)
_pipeline = AdaptiveAssemblyPipeline(_ranking_service, _embedding_service)
audit_manager = RuntimeAuditTrailManager()
lineage_engine = SemanticLineageEngine()
policy_engine = GovernancePolicyEngine()
observability_manager = OperationalObservabilityManager()
integrity_monitor = RuntimeIntegrityMonitor()

_integrated_runtime = IntegratedRuntimeSystem(
    _pipeline, 
    lineage_engine=lineage_engine, 
    audit_manager=audit_manager
)
sdk = MemLayerSDK(_integrated_runtime)


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

@router.get("/compiler/pipeline")
def get_compiler_pipeline():
    history = [r.to_dict() for r in _pipeline.execution_history[-10:]]
    # Also include the analytics summary
    analytics = _pipeline.get_analytics_report()
    return {"history": history, "analytics": analytics}

@router.get("/telemetry")
def get_telemetry():
    return sdk.get_telemetry()

@router.get("/telemetry/coordination-traces")
def get_coordination_traces(limit: int = 50):
    return sdk._integrated_runtime.telemetry.get_coordination_traces(limit=limit)

@router.get("/views/cached")
def get_cached_views():
    # Return all cached views across all workspaces for visualization
    workspaces = sdk.workspaces.list_workspaces()
    all_views = []
    
    for ws in workspaces:
        ws_id = ws["workspace_id"]
        try:
            ws_obj = sdk.workspaces.get_workspace(ws_id)
            if ws_obj.snapshots:
                latest_snap = ws_obj.snapshots[-1]
                # Assuming state property or similar exists on snapshot
                # In phase 8, snapshots have get_semantic_state or similar, but
                # we can just use the view_api get_diagnostics which exposes shared_state_summary
                pass
        except Exception:
            continue
            
    # Actually, sdk.views.get_diagnostics() contains "context_bus" which has all the cached projections
    return sdk.views.get_diagnostics()

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
    # Fetch lineage data across workspaces or a specific workspace
    target_workspaces = [workspace_id] if workspace_id else [ws["workspace_id"] for ws in sdk.workspaces.list_workspaces()]
    
    nodes = []
    edges = []
    
    for ws_id in target_workspaces:
        checkpoints = lineage_engine.get_checkpoints_for_workspace(ws_id, tenant_id)
        for cp in checkpoints:
            nodes.append({
                "id": cp.checkpoint_id,
                "label": f"Checkpoint\n{cp.operation_id}",
                "timestamp": cp.timestamp,
                "hash": cp.semantic_state_hash[:8]
            })
            for parent_id in cp.derived_from:
                edges.append({
                    "source": parent_id,
                    "target": cp.checkpoint_id
                })
                
    return {"nodes": nodes, "edges": edges}

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
    cp1 = lineage_engine.record_semantic_checkpoint(
        workspace_id=ws1.workspace_id,
        semantic_state={"nodes": 10, "edges": 15},
        operation_id="initial_compilation",
        tenant_id="default"
    )
    cp2 = lineage_engine.record_semantic_checkpoint(
        workspace_id=ws1.workspace_id,
        semantic_state={"nodes": 12, "edges": 18},
        operation_id="market_analysis",
        derived_from=[cp1.checkpoint_id],
        tenant_id="default"
    )
    
    audit_manager.record_event(
        workspace_id=ws1.workspace_id,
        event_type="WORKSPACE_CREATED",
        event_data={"provider": "claude"},
        recorded_by="system",
        tenant_id="default"
    )
    audit_manager.record_event(
        workspace_id=ws1.workspace_id,
        event_type="POLICY_ENFORCEMENT",
        event_data={"policy": "TokenBudgetLimit", "status": "passed"},
        recorded_by="policy_engine",
        tenant_id="default"
    )
    audit_manager.record_event(
        workspace_id=ws1.workspace_id,
        event_type="SEMANTIC_CHECKPOINT",
        event_data={"checkpoint_id": cp2.checkpoint_id},
        recorded_by="LineageEngine",
        tenant_id="default"
    )
    
    observability_manager.record_health_metric("default", "SharedAgentRuntime", 0.95, {"latency": 450})
    observability_manager.record_health_metric("default", "ViewEngineCompiler", 0.99, {"cache_hit_rate": 0.85})
    observability_manager.record_health_metric("default", "GovernancePolicyEngine", 1.0, {"policies_enforced": 12})
    observability_manager.record_health_metric("default", "RuntimeIntegrityMonitor", 0.98, {"checks_passed": 100})
    
    return {"status": "seeded"}
@router.post("/ingest-locomo")
def ingest_locomo_dataset(payload: Dict[str, Any]):
    """
    Ingests the LoCoMo dataset into the runtime.
    Creates isolated workspaces for longitudinal evaluation.
    """
    dataset_path = payload.get("dataset_path", "/Users/overcoder/Code/memlayer/Dataset/locomo10.json")
    workspace_prefix = payload.get("workspace_prefix", "locomo-eval")
    num_samples = payload.get("num_samples", 1)
    
    import json
    from pathlib import Path
    
    path = Path(dataset_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Dataset not found at {path}")
        
    with open(path, "r") as f:
        data = json.load(f)
        
    results = []
    
    for s_idx in range(min(num_samples, len(data))):
        sample = data[s_idx]
        ws_id = f"{workspace_prefix}-{s_idx}-{uuid.uuid4().hex[:4]}"
        conversation = sample["conversation"]
        
        # Create workspace
        sdk.create_workspace(workspace_id=ws_id, provider="openai")
        
        session_results = []
        
        # Ingest sessions chronologically (up to 35 sessions in LoCoMo)
        for i in range(1, 36):
            session_key = f"session_{i}"
            date_key = f"session_{i}_date_time"
            
            if session_key not in conversation:
                continue
                
            session_data = conversation[session_key]
            timestamp = conversation.get(date_key, datetime.now(timezone.utc).isoformat())
            
            memories = []
            for utt in session_data:
                memories.append({
                    "id": utt["dia_id"],
                    "content": utt["text"],
                    "metadata": {
                        "speaker": utt["speaker"],
                        "session": i,
                        "timestamp": timestamp,
                        "dia_id": utt["dia_id"]
                    }
                })
                
            # Add memories
            sdk.add_memories(ws_id, memories)
            
            # Run coordination to trigger runtime systems (Lineage, Telemetry, etc.)
            # We vary the query to simulate evolution
            query = f"What were the key updates in session {i} compared to previous sessions?"
            if i == 1:
                query = "Initialize the conversation state and summarize the first meeting."
                
            sdk.coordinate(ws_id, query)
            
            session_results.append({
                "session": i,
                "utterances": len(session_data)
            })
            
        results.append({
            "workspace_id": ws_id,
            "sessions": len(session_results)
        })
        
    return {"status": "ingested", "workspaces": results}
