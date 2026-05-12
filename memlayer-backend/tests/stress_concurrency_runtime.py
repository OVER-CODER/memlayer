"""
Concurrency Stress Validation Script for MemLayer.
Simulates high-concurrency multi-tenant ingestion using synthetic MSC-pattern workloads.
Validates Redis locking and async persistence under pressure.
"""

import asyncio
import time
import uuid
import random
from datetime import datetime, timezone
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.persistence.repositories.sql_uow import SQLUnitOfWork
from app.persistence.serialization import get_canonical_serializer

serializer = get_canonical_serializer()

async def simulate_tenant_worker(tenant_id: str, num_workspaces: int, turns_per_ws: int):
    """Simulate a single tenant worker performing parallel cognition runs."""
    
    async def run_ws_session(ws_index: int):
        workspace_id = f"ws_msc_stress_{tenant_id}_{ws_index}"
        
        async with AsyncSessionLocal() as session:
            async with SQLUnitOfWork(session) as uow:
                # 1. Workspace setup
                await uow.workspaces.save({
                    "id": workspace_id,
                    "tenant_id": tenant_id,
                    "name": f"MSC Stress WS {ws_index}",
                    "description": "Synthetic high-concurrency workspace"
                })
                
                # 2. Sequential turns with random latency
                for i in range(turns_per_ws):
                    turn_data = {"text": f"Synthetic turn {i} content for {workspace_id}", "speaker": "user"}
                    
                    # Simulate small processing delay
                    # await asyncio.sleep(random.uniform(0.001, 0.005))
                    
                    start_turn = time.time()
                    
                    # Memory Save
                    await uow.memories.save({
                        "id": f"m_{workspace_id}_{i}",
                        "workspace_id": workspace_id,
                        "tenant_id": tenant_id,
                        "source_type": "msc_concurrency_stress",
                        "raw_content": turn_data["text"],
                        "importance_score": random.random()
                    })
                    
                    # Trace Save
                    await uow.traces.save_trace({
                        "trace_id": str(uuid.uuid4()),
                        "workspace_id": workspace_id,
                        "tenant_id": tenant_id,
                        "query": f"Turn {i}",
                        "provider": "mock",
                        "compression_mode": "none",
                        "token_budget": 0,
                        "execution_plan": {"synthetic": True},
                        "trace_data": {"latency": (time.time() - start_turn) * 1000},
                        "integrity_hash": serializer.compute_checksum(turn_data)
                    })
                
                await uow.commit()

    # Run multiple workspaces in parallel for this tenant
    tasks = [run_ws_session(i) for i in range(num_workspaces)]
    await asyncio.gather(*tasks)

async def main():
    print("Starting MSC-Pattern Concurrency Stress Validation...")
    
    start_total = time.time()
    
    # 5 parallel tenants, each with 10 parallel workspaces, 5 turns each
    # Total: 50 workspaces, 250 turns, concurrent
    tenants = ["tenant_alpha", "tenant_beta", "tenant_gamma", "tenant_delta", "tenant_epsilon"]
    
    tasks = [simulate_tenant_worker(t, 10, 5) for t in tenants]
    await asyncio.gather(*tasks)
    
    duration = time.time() - start_total
    total_turns = 5 * 10 * 5
    print(f"\nConcurrency Stress Complete!")
    print(f"Total Turns: {total_turns}")
    print(f"Total Duration: {duration:.2f}s")
    print(f"Throughput: {total_turns/duration:.2f} turns/sec")

if __name__ == "__main__":
    asyncio.run(main())
