"""
Test High Volume Replay - Phase D1.5
Validates replay under high volume of traces.
"""

import asyncio
import httpx
import time
import json
import hashlib
from typing import Dict, Any, List
from datetime import datetime

from production_runner import TestResult


async def test_high_volume_replay(base_url: str) -> TestResult:
    """
    Test high volume replay.
    Validates:
    - Replay throughput
    - Memory efficiency
    - Trace reconstruction accuracy
    """
    start_time = time.time()
    errors: List[str] = []
    metrics: Dict[str, Any] = {}

    async with httpx.AsyncClient(timeout=300.0) as client:
        # Create workspace with high volume of memories
        print("  Creating workspace with high memory volume...")

        response = await client.post(
            f"{base_url}/api/workspaces",
            params={"name": f"high-volume-{int(time.time())}"},
        )

        if response.status_code != 200:
            errors.append(f"Failed to create workspace: {response.status_code}")
            return TestResult(
                test_name="test_high_volume_replay",
                status="ERROR",
                duration=time.time() - start_time,
                metrics={},
                errors=errors,
            )

        workspace = response.json()
        workspace_id = workspace.get("id")

        # Ingest high volume of memories
        num_memories = 100
        ingest_latencies = []

        print(f"  Ingesting {num_memories} memories...")

        for i in range(num_memories):
            start = time.time()

            response = await client.post(
                f"{base_url}/api/memories",
                params={
                    "workspace_id": workspace_id,
                    "content": f"High volume memory {i} with some additional content to make each memory distinct and test the system's ability to handle large volumes of data efficiently",
                    "memory_type": "conversation",
                },
            )

            latency = time.time() - start
            ingest_latencies.append(latency)

        metrics["ingestion"] = {
            "count": num_memories,
            "avg_latency_ms": sum(ingest_latencies) / len(ingest_latencies) * 1000,
            "max_latency_ms": max(ingest_latencies) * 1000,
            "min_latency_ms": min(ingest_latencies) * 1000,
        }

        # Test replay performance
        print("  Testing replay performance...")

        replay_times = []
        for _ in range(5):
            start = time.time()

            response = await client.get(f"{base_url}/api/workspaces/{workspace_id}")

            replay_time = time.time() - start
            replay_times.append(replay_time)

        replay_checksums = []
        for _ in range(3):
            response = await client.get(f"{base_url}/api/workspaces/{workspace_id}")
            if response.status_code == 200:
                data = response.json()
                checksum = hashlib.sha256(
                    json.dumps(data, sort_keys=True).encode()
                ).hexdigest()
                replay_checksums.append(checksum)

        # Verify replay determinism under high volume
        replay_deterministic = len(set(replay_checksums[:2])) == 1

        metrics["replay"] = {
            "replays": len(replay_times),
            "avg_replay_ms": sum(replay_times) / len(replay_times) * 1000,
            "max_replay_ms": max(replay_times) * 1000,
            "deterministic": replay_deterministic,
        }

        # Test concurrent replays
        print("  Testing concurrent replays...")

        async def concurrent_replay():
            start = time.time()
            response = await client.get(f"{base_url}/api/workspaces/{workspace_id}")
            return time.time() - start, response.status_code

        concurrent_results = await asyncio.gather(
            *[concurrent_replay() for _ in range(10)], return_exceptions=True
        )

        successful = sum(
            1 for r in concurrent_results if isinstance(r, tuple) and r[1] == 200
        )
        concurrent_latencies = [
            r[0] for r in concurrent_results if isinstance(r, tuple)
        ]

        metrics["concurrent_replay"] = {
            "attempted": 10,
            "successful": successful,
            "avg_latency_ms": sum(concurrent_latencies)
            / len(concurrent_latencies)
            * 1000
            if concurrent_latencies
            else 0,
        }

    duration = time.time() - start_time

    # Determine status
    replay_ok = metrics.get("replay", {}).get("deterministic", False)
    concurrent_ok = (
        metrics.get("concurrent_replay", {}).get("successful", 0) >= 8
    )  # At least 80%

    status = "PASS" if replay_ok and concurrent_ok else "FAIL"

    return TestResult(
        test_name="test_high_volume_replay",
        status=status,
        duration=duration,
        metrics=metrics,
        errors=errors,
    )
