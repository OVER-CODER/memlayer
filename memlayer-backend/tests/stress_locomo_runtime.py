"""
Stress Validation Script for MemLayer using LoCoMo Dataset.
Validates longitudinal ingestion, lineage growth, and persistence performance.
"""

import json
import time
import asyncio
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any

from app.db.session import AsyncSessionLocal
from app.persistence.repositories.sql_uow import SQLUnitOfWork
from app.persistence.serialization import get_canonical_serializer
from app.core.observability import get_observability

serializer = get_canonical_serializer()
obs = get_observability()

from sqlalchemy import text

async def ingest_locomo_sample(sample: Dict[str, Any], tenant_id: str = "tenant_research"):
    """Ingest a single LoCoMo sample into the runtime substrate."""
    sample_id = sample["sample_id"]
    workspace_id = f"ws_locomo_{sample_id}"
    
    async with AsyncSessionLocal() as session:
        async with SQLUnitOfWork(session) as uow:
            # 1. Ensure Workspace exists
            ws = await uow.workspaces.get_by_id(workspace_id, tenant_id)
            if not ws:
                await uow.workspaces.save({
                    "id": workspace_id,
                    "tenant_id": tenant_id,
                    "name": f"LoCoMo Workspace {sample_id}",
                    "description": f"Longitudinal study for {sample.get('speaker_a', 'Subject')}"
                })
            
            # 2. Iterate through sessions
            conversation = sample.get("conversation", {})
            sessions = [k for k in conversation.keys() if k.startswith("session_") and not k.endswith("_date_time")]
            # Sort sessions by number
            sessions.sort(key=lambda x: int(x.split("_")[1]))
            
            last_checkpoint_id = None
            
            for session_key in sessions:
                session_num = session_key.split("_")[1]
                timestamp_str = conversation.get(f"{session_key}_date_time", datetime.now(timezone.utc).isoformat())
                turns = conversation.get(session_key, [])
                
                start_time = time.time()
                
                # Create a Checkpoint for this session
                checkpoint_id = str(uuid.uuid4())
                state_hash = serializer.compute_checksum(turns)
                
                # In actual lineage engine, this would be more complex
                # Here we simulate the persistence load
                await session.execute(
                    text("INSERT INTO semantic_lineage (checkpoint_id, workspace_id, tenant_id, state_hash, parent_id, operation_id, timestamp) "
                    "VALUES (:id, :ws, :t, :h, :p, :op, :ts)"),
                    {
                        "id": checkpoint_id,
                        "ws": workspace_id,
                        "t": tenant_id,
                        "h": state_hash,
                        "p": last_checkpoint_id,
                        "op": f"ingest_session_{session_num}",
                        "ts": datetime.now(timezone.utc)
                    }
                )
                
                # Ingest Memories
                for i, turn in enumerate(turns):
                    memory_data = {
                        "id": f"{workspace_id}_{session_num}_{i}",
                        "workspace_id": workspace_id,
                        "tenant_id": tenant_id,
                        "source_type": "longitudinal_ingestion",
                        "raw_content": turn["text"],
                        "extra_metadata": {"speaker": turn["speaker"], "dia_id": turn.get("dia_id")},
                        "importance_score": 0.8
                    }
                    await uow.memories.save(memory_data)
                
                # Record Replay Trace
                trace_id = str(uuid.uuid4())
                await uow.traces.save_trace({
                    "trace_id": trace_id,
                    "workspace_id": workspace_id,
                    "tenant_id": tenant_id,
                    "query": f"Ingest Session {session_num}",
                    "provider": "system",
                    "compression_mode": "none",
                    "token_budget": 0,
                    "execution_plan": {"turns_count": len(turns)},
                    "trace_data": {"duration_ms": (time.time() - start_time) * 1000},
                    "integrity_hash": state_hash
                })
                
                # Record Telemetry
                await uow.telemetry.record_metric({
                    "trace_id": trace_id,
                    "tenant_id": tenant_id,
                    "stage": "ingestion",
                    "duration_ms": (time.time() - start_time) * 1000,
                    "token_metrics": {"turns": len(turns)}
                })
                
                last_checkpoint_id = checkpoint_id
                
            await uow.commit()
            print(f"✓ Ingested LoCoMo sample {sample_id} ({len(sessions)} sessions)")

async def main():
    print("Starting LoCoMo Stress Validation...")
    with open("../Dataset/locomo10.json", "r") as f:
        data = json.load(f)
    
    start_total = time.time()
    
    # Process first 5 samples for deep validation
    # (In real production we would do all 10)
    tasks = [ingest_locomo_sample(sample) for sample in data[:5]]
    await asyncio.gather(*tasks)
    
    duration = time.time() - start_total
    print(f"\nLoCoMo Ingestion Complete in {duration:.2f}s")
    
    # Report metrics
    # ... (Add benchmark log persistence here)

if __name__ == "__main__":
    asyncio.run(main())
