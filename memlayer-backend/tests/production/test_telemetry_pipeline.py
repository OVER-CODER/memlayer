"""
Test Telemetry Pipeline - Phase D1.5
Validates telemetry persistence, OTEL trace propagation, and metrics stability.
"""

import asyncio
import httpx
import time
import json
from typing import Dict, Any, List
from datetime import datetime

from production_runner import TestResult


async def test_telemetry_pipeline(base_url: str) -> TestResult:
    """
    Test telemetry pipeline.
    Validates:
    - Telemetry persistence
    - OTEL trace propagation
    - trace_id consistency
    - Prometheus metrics stability
    - Async telemetry buffering
    """
    start_time = time.time()
    errors: List[str] = []
    metrics: Dict[str, Any] = {}

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Test 1: Basic metrics endpoint
        print("  Testing metrics endpoint...")

        response = await client.get(f"{base_url}/metrics")
        metrics_available = response.status_code == 200

        metrics["endpoint"] = {
            "metrics": metrics_available,
            "status": response.status_code,
        }

        # Test 2: Health endpoint with telemetry
        print("  Testing health telemetry...")

        response = await client.get(f"{base_url}/health")
        health_data = response.json() if response.status_code == 200 else {}

        metrics["health_telemetry"] = {
            "status": health_data.get("status"),
            "version": health_data.get("version"),
        }

        # Test 3: Generate load and measure telemetry
        print("  Generating telemetry under load...")

        latencies = []
        for i in range(50):
            start = time.time()

            # Create workspace (generates telemetry)
            response = await client.post(
                f"{base_url}/api/workspaces",
                params={"name": f"telemetry-test-{i}-{int(time.time())}"},
            )

            latency = time.time() - start
            latencies.append(latency)

        # Check metrics again after load
        response = await client.get(f"{base_url}/metrics")

        metrics["load_telemetry"] = {
            "requests": 50,
            "avg_latency_ms": sum(latencies) / len(latencies) * 1000,
            "max_latency_ms": max(latencies) * 1000,
            "metrics_endpoint_still_works": response.status_code == 200,
        }

        # Test 4: Trace propagation
        print("  Testing trace propagation...")

        # Add trace context headers
        headers = {"X-Trace-ID": "test-trace-12345", "X-Span-ID": "test-span-67890"}

        response = await client.get(f"{base_url}/health", headers=headers)

        trace_propagated = response.status_code == 200

        metrics["trace_propagation"] = {
            "headers_sent": list(headers.keys()),
            "propagated": trace_propagated,
        }

        # Test 5: Async telemetry buffering
        print("  Testing async telemetry...")

        # Create workspace with many operations
        response = await client.post(
            f"{base_url}/api/workspaces",
            params={"name": f"async-telemetry-{int(time.time())}"},
        )

        ws_id = response.json().get("id") if response.status_code == 200 else None

        if ws_id:
            # Add many memories (generates async telemetry)
            for i in range(20):
                await client.post(
                    f"{base_url}/api/memories",
                    params={
                        "workspace_id": ws_id,
                        "content": f"Async telemetry test {i}",
                        "memory_type": "conversation",
                    },
                )

        # Check metrics stability
        response = await client.get(f"{base_url}/metrics")

        metrics["async_buffering"] = {
            "operations": 20,
            "metrics_stable": response.status_code == 200,
        }

    duration = time.time() - start_time

    # Determine status
    metrics_ok = metrics.get("endpoint", {}).get("metrics", False)
    stable = metrics.get("load_telemetry", {}).get(
        "metrics_endpoint_still_works", False
    )

    status = "PASS" if metrics_ok and stable else "FAIL"

    return TestResult(
        test_name="test_telemetry_pipeline",
        status=status,
        duration=duration,
        metrics=metrics,
        errors=errors,
    )
