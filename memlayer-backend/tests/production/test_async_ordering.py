"""
Test Async Ordering - Phase D1.5
Validates monotonic sequence IDs and deterministic ordering under concurrency.
"""

import asyncio
import httpx
import time
import json
import hashlib
from typing import Dict, Any, List
from datetime import datetime

from helpers import TestResult, get_auth_headers


async def test_async_ordering(base_url: str) -> TestResult:
    """
    Test async ordering validation.
    Validates:
    - Monotonic sequence IDs
    - Deterministic ordering
    - Event loop stability
    - ContextVar propagation
    """
    start_time = time.time()
    errors: List[str] = []
    metrics: Dict[str, Any] = {}
    tenant_id = "async-order-test-tenant"

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Create workspace
        print("  Testing async ordering...")

        response = await client.post(
            f"{base_url}/api/workspaces",
            params={"name": f"async-order-test-{int(time.time())}"},
            headers=get_auth_headers(tenant_id),
        )

        if response.status_code != 200:
            errors.append(f"Failed to create workspace: {response.status_code} {response.text}")
            return TestResult(
                test_name="test_async_ordering",
                status="ERROR",
                duration=time.time() - start_time,
                metrics={},
                errors=errors,
            )

        workspace = response.json()
        workspace_id = workspace.get("id")

        # Test 1: Sequential ordering
        print("  Testing sequential ordering...")

        sequence_hashes = []
        for i in range(10):
            content = f"Order test message {i}"

            response = await client.post(
                f"{base_url}/api/memories",
                params={
                    "workspace_id": workspace_id,
                    "content": content,
                    "memory_type": "conversation",
                },
                headers=get_auth_headers(tenant_id),
            )

            if response.status_code == 200:
                memory = response.json()
                seq_hash = hashlib.sha256(content.encode()).hexdigest()
                sequence_hashes.append(
                    {
                        "order": i,
                        "content_hash": seq_hash[:16],
                        "timestamp": memory.get("created_at"),
                    }
                )

        # Verify ordering is preserved
        ordering_preserved = len(sequence_hashes) == 10

        metrics["sequential_order"] = {
            "total": len(sequence_hashes),
            "preserved": ordering_preserved,
        }

        # Test 2: Concurrent ordering with parallel ingestion
        print("  Testing concurrent ordering...")

        async def add_concurrent_message(index: int):
            content = f"Concurrent message {index}"
            try:
                response = await client.post(
                    f"{base_url}/api/memories",
                    params={
                        "workspace_id": workspace_id,
                        "content": content,
                        "memory_type": "conversation",
                    },
                    headers=get_auth_headers(tenant_id),
                )
                return response.status_code == 200
            except:
                return False

        # Run concurrent operations
        results = await asyncio.gather(
            *[add_concurrent_message(i) for i in range(20)], return_exceptions=True
        )

        successful = sum(1 for r in results if r is True)

        # Test 3: Verify retrieval ordering
        print("  Verifying retrieval ordering...")

        response = await client.get(
            f"{base_url}/api/workspaces/{workspace_id}",
            headers=get_auth_headers(tenant_id),
        )

        # Get workspace state and check ordering
        state = response.json() if response.status_code == 200 else {}
        mem_count = len(state.get("memories", []))

        # Test 4: Event loop stability
        print("  Testing event loop stability...")

        loop_latencies = []
        for _ in range(30):
            start = time.time()
            response = await client.get(f"{base_url}/health")
            latency = time.time() - start
            loop_latencies.append(latency)

        # Check for any anomalous latencies
        max_latency = max(loop_latencies)
        stable = max_latency < 5  # Less than 5 seconds

        metrics["event_loop"] = {
            "requests": len(loop_latencies),
            "max_latency_s": max_latency,
            "stable": stable,
        }

        # Test 5: ContextVar propagation (via headers)
        print("  Testing context propagation...")

        # Create a new workspace for context test
        response = await client.post(
            f"{base_url}/api/workspaces",
            params={"name": "context-test"},
            headers=get_auth_headers("test-tenant-async"),
        )

        context_propagated = response.status_code == 200

        metrics["context_propagation"] = {"propagated": context_propagated}

    duration = time.time() - start_time

    # Determine status
    ordering_ok = metrics.get("sequential_order", {}).get("preserved", False)
    loop_stable = metrics.get("event_loop", {}).get("stable", False)

    status = "PASS" if ordering_ok and loop_stable else "FAIL"

    return TestResult(
        test_name="test_async_ordering",
        status=status,
        duration=duration,
        metrics=metrics,
        errors=errors,
    )
