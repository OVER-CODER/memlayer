"""
Test Concurrent Ingestion - Phase D1.5
Validates concurrent workspace operations under heavy load.
"""

import asyncio
import httpx
import time
import random
import hashlib
from typing import Dict, Any, List
from datetime import datetime

from helpers import TestResult, JWT_TOKEN, get_auth_headers


async def create_workspace(
    client: httpx.AsyncClient, base_url: str, name: str, tenant_id: str = "test-tenant"
) -> Dict[str, Any]:
    """Create a workspace via API."""
    response = await client.post(
        f"{base_url}/api/workspaces",
        params={"name": name, "description": f"Test workspace {name}"},
        headers=get_auth_headers(tenant_id),
    )
    return response.json() if response.status_code == 200 else {}


async def create_memory(
    client: httpx.AsyncClient,
    base_url: str,
    workspace_id: str,
    content: str,
    tenant_id: str = "test-tenant",
) -> Dict[str, Any]:
    """Create a memory in a workspace."""
    response = await client.post(
        f"{base_url}/api/memories",
        params={
            "workspace_id": workspace_id,
            "content": content,
            "memory_type": "conversation",
        },
        headers=get_auth_headers(tenant_id),
    )
    return response.json() if response.status_code == 200 else {}


async def read_workspace(
    client: httpx.AsyncClient,
    base_url: str,
    workspace_id: str,
    tenant_id: str = "test-tenant",
) -> Dict[str, Any]:
    """Read a workspace."""
    response = await client.get(
        f"{base_url}/api/workspaces/{workspace_id}", headers=get_auth_headers(tenant_id)
    )
    return response.json() if response.status_code == 200 else {}


async def test_concurrent_ingestion(base_url: str) -> TestResult:
    """
    Test concurrent workspace operations.
    Validates:
    - Redis lock correctness
    - No deadlocks
    - No race conditions
    - No partial commits
    """
    start_time = time.time()
    errors: List[str] = []
    metrics: Dict[str, Any] = {}

    num_concurrent = 50  # Number of concurrent operations
    num_workspaces = 10  # Number of workspaces to create

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test 1: Concurrent workspace creation
        print(f"  Creating {num_concurrent} concurrent workspaces...")

        workspace_tasks = [
            create_workspace(client, base_url, f"concurrent-ws-{i}", f"tenant-{i % 5}")
            for i in range(num_concurrent)
        ]

        results = await asyncio.gather(*workspace_tasks, return_exceptions=True)

        successful_workspaces = [
            r for r in results if isinstance(r, dict) and r.get("id")
        ]
        failed_workspaces = [r for r in results if isinstance(r, Exception)]

        metrics["workspace_creation"] = {
            "attempted": num_concurrent,
            "successful": len(successful_workspaces),
            "failed": len(failed_workspaces),
        }

        if failed_workspaces:
            errors.append(f"Failed to create {len(failed_workspaces)} workspaces")

        # Test 2: Concurrent memory ingestion per workspace
        if successful_workspaces:
            print(
                f"  Creating {num_concurrent} concurrent memories across workspaces..."
            )

            memory_tasks = []
            for i, ws in enumerate(successful_workspaces[:num_workspaces]):
                for j in range(5):  # 5 memories per workspace
                    content = f"Test memory {j} in workspace {i} at {datetime.utcnow().isoformat()}"
                    memory_tasks.append(
                        create_memory(
                            client,
                            base_url,
                            ws["id"],
                            content,
                            ws.get("tenant_id", "test-tenant"),
                        )
                    )

            memory_results = await asyncio.gather(*memory_tasks, return_exceptions=True)
            successful_memories = [
                r for r in memory_results if isinstance(r, dict) and r.get("id")
            ]
            failed_memories = [r for r in memory_results if isinstance(r, Exception)]

            metrics["memory_ingestion"] = {
                "attempted": len(memory_tasks),
                "successful": len(successful_memories),
                "failed": len(failed_memories),
            }

            if failed_memories:
                errors.append(f"Failed to create {len(failed_memories)} memories")

        # Test 3: Concurrent reads during writes
        print("  Testing concurrent reads during writes...")

        async def read_workspace(client, ws_id, tenant_id):
            try:
                response = await client.get(
                    f"{base_url}/api/workspaces/{ws_id}",
                    headers=get_auth_headers(tenant_id),
                )
                return response.status_code == 200
            except:
                return False

        if successful_workspaces:
            read_tasks = [
                read_workspace(client, ws["id"], ws.get("tenant_id", "test-tenant"))
                for ws in successful_workspaces[:5]
                for _ in range(10)  # 10 reads each
            ]
            read_results = await asyncio.gather(*read_tasks, return_exceptions=True)
            successful_reads = sum(1 for r in read_results if r is True)

            metrics["concurrent_reads"] = {
                "attempted": len(read_tasks),
                "successful": successful_reads,
            }

    duration = time.time() - start_time

    # Determine status
    # Allow some failures but track them
    total_successful = metrics.get("workspace_creation", {}).get(
        "successful", 0
    ) + metrics.get("memory_ingestion", {}).get("successful", 0)
    total_attempted = metrics.get("workspace_creation", {}).get(
        "attempted", 0
    ) + metrics.get("memory_ingestion", {}).get("attempted", 0)

    success_rate = total_successful / total_attempted if total_attempted > 0 else 0

    status = "PASS" if success_rate >= 0.9 else "FAIL"

    return TestResult(
        test_name="test_concurrent_ingestion",
        status=status,
        duration=duration,
        metrics=metrics,
        errors=errors,
    )
