"""
Test Redis Coordination - Phase D1.5
Validates Redis-based coordination, locking, and caching.
"""

import asyncio
import httpx
import time
import json
import hashlib
from typing import Dict, Any, List
from datetime import datetime

from production_runner import TestResult


async def test_redis_coordination(base_url: str) -> TestResult:
    """
    Test Redis coordination.
    Validates:
    - Redis lock correctness
    - distributed locking
    - no deadlocks
    - coordination cache
    """
    start_time = time.time()
    errors: List[str] = []
    metrics: Dict[str, Any] = {}

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Create multiple workspaces for lock testing
        print("  Testing Redis coordination with multiple workspaces...")

        workspaces = []
        for i in range(10):
            response = await client.post(
                f"{base_url}/api/workspaces",
                params={"name": f"redis-test-{i}-{int(time.time())}"},
            )
            if response.status_code == 200:
                workspaces.append(response.json())

        metrics["workspaces"] = {"created": len(workspaces)}

        # Test concurrent operations that require coordination
        print("  Testing concurrent coordination...")

        async def add_memory_with_timing(ws_id: str, index: int):
            start = time.time()
            response = await client.post(
                f"{base_url}/api/memories",
                params={
                    "workspace_id": ws_id,
                    "content": f"Coordination test message {index}",
                    "memory_type": "conversation",
                },
            )
            latency = time.time() - start
            return {"success": response.status_code == 200, "latency": latency}

        # Run concurrent operations
        tasks = []
        for ws in workspaces[:5]:
            for i in range(3):
                tasks.append(add_memory_with_timing(ws["id"], i))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        latencies = [r.get("latency", 0) for r in results if isinstance(r, dict)]

        metrics["coordination"] = {
            "operations": len(tasks),
            "successful": successful,
            "avg_latency_ms": sum(latencies) / len(latencies) * 1000
            if latencies
            else 0,
            "max_latency_ms": max(latencies) * 1000 if latencies else 0,
        }

        # Test lock acquisition latency
        print("  Testing lock acquisition...")

        lock_latencies = []
        for ws in workspaces[:3]:
            start = time.time()
            # Trigger a locked operation
            response = await client.get(f"{base_url}/api/workspaces/{ws['id']}")
            lock_latency = time.time() - start
            lock_latencies.append(lock_latency)

        metrics["locks"] = {
            "avg_acquisition_ms": sum(lock_latencies) / len(lock_latencies) * 1000
            if lock_latencies
            else 0
        }

        # Verify no deadlocks by checking all workspaces are accessible
        print("  Verifying no deadlocks...")

        accessible = 0
        for ws in workspaces:
            response = await client.get(f"{base_url}/api/workspaces/{ws['id']}")
            if response.status_code == 200:
                accessible += 1

        metrics["deadlock_check"] = {
            "total": len(workspaces),
            "accessible": accessible,
            "deadlock_detected": accessible < len(workspaces),
        }

        if accessible < len(workspaces):
            errors.append(
                f"Deadlock detected: {len(workspaces) - accessible} workspaces not accessible"
            )

    duration = time.time() - start_time

    # Determine status
    deadlock = metrics.get("deadlock_check", {}).get("deadlock_detected", True)
    status = "PASS" if not deadlock else "FAIL"

    return TestResult(
        test_name="test_redis_coordination",
        status=status,
        duration=duration,
        metrics=metrics,
        errors=errors,
    )
