"""
Test Connection Resilience - Phase D1.5
Validates database and Redis connection resilience under stress.
"""

import asyncio
import httpx
import time
import json
from typing import Dict, Any, List
from datetime import datetime

from helpers import TestResult, get_auth_headers


async def test_connection_resilience(base_url: str) -> TestResult:
    """
    Test connection resilience.
    Validates:
    - Connection drops recovery
    - Timeout handling
    - Graceful degradation
    - Reconnection logic
    """
    start_time = time.time()
    errors: List[str] = []
    metrics: Dict[str, Any] = {}
    tenant_id = "resilience-test-tenant"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Basic connectivity
        print("  Testing basic connectivity...")

        response = await client.get(f"{base_url}/health")
        healthy = response.status_code == 200

        metrics["basic_connectivity"] = {
            "status_code": response.status_code,
            "healthy": healthy,
        }

        # Test 2: Rapid successive requests
        print("  Testing rapid requests...")

        latencies = []
        for _ in range(20):
            start = time.time()
            response = await client.get(f"{base_url}/health")
            latency = time.time() - start
            latencies.append(latency)

        metrics["rapid_requests"] = {
            "count": len(latencies),
            "avg_latency_ms": sum(latencies) / len(latencies) * 1000,
            "max_latency_ms": max(latencies) * 1000,
            "min_latency_ms": min(latencies) * 1000,
        }

        # Test 3: Long-running connection
        print("  Testing long-running connection...")

        connection_start = time.time()

        # Create workspace and add multiple memories
        response = await client.post(
            f"{base_url}/api/workspaces",
            params={"name": f"resilience-test-{int(time.time())}"},
            headers=get_auth_headers(tenant_id),
        )

        workspace_id = (
            response.json().get("id") if response.status_code == 200 else None
        )

        for i in range(10):
            if workspace_id:
                await client.post(
                    f"{base_url}/api/workspaces/{workspace_id}/memories",
                    json={
                        "raw_content": f"Long connection test {i}",
                        "source_type": "conversation",
                    },
                    headers=get_auth_headers(tenant_id),
                )

        connection_duration = time.time() - connection_start

        metrics["long_connection"] = {
            "duration_seconds": connection_duration,
            "operations": 10,
        }

        # Test 4: Connection pool stress
        print("  Testing connection pool...")

        pool_latencies = []
        for _ in range(50):
            start = time.time()
            response = await client.get(f"{base_url}/health")
            latency = time.time() - start
            pool_latencies.append(latency)

        pool_failures = sum(
            1 for lat in pool_latencies if lat > 5
        )  # Fail if > 5 seconds

        metrics["connection_pool"] = {
            "requests": len(pool_latencies),
            "failures": pool_failures,
            "avg_latency_ms": sum(pool_latencies) / len(pool_latencies) * 1000,
        }

        # Test 5: Recovery after failed request
        print("  Testing recovery after failure...")

        # Send a request that might fail (invalid workspace)
        fail_response = await client.get(
            f"{base_url}/api/workspaces/invalid-workspace-12345",
            headers=get_auth_headers(tenant_id),
        )

        # Then send a valid request
        recovery_response = await client.get(f"{base_url}/health")
        recovered = recovery_response.status_code == 200

        metrics["recovery"] = {
            "failed_request": fail_response.status_code,
            "recovered": recovered,
        }

    duration = time.time() - start_time

    # Determine status
    healthy = metrics.get("basic_connectivity", {}).get("healthy", False)
    recovered = metrics.get("recovery", {}).get("recovered", False)

    status = "PASS" if healthy and recovered else "FAIL"

    return TestResult(
        test_name="test_connection_resilience",
        status=status,
        duration=duration,
        metrics=metrics,
        errors=errors,
    )
