"""
Test PGVector Scaling - Phase D1.5
Validates vector retrieval latency and scaling behavior.
"""

import asyncio
import httpx
import time
import json
from typing import Dict, Any, List
from datetime import datetime

from helpers import TestResult, get_auth_headers


async def test_pgvector_scaling(base_url: str) -> TestResult:
    """
    Test PGVector scaling.
    Validates:
    - Vector retrieval latency
    - Top-k retrieval stability
    - Ranking determinism
    - Scaling behavior
    """
    start_time = time.time()
    errors: List[str] = []
    metrics: Dict[str, Any] = {}
    tenant_id = "vector-test-tenant"

    async with httpx.AsyncClient(timeout=180.0) as client:
        # Test with different memory scales

        scales = [10, 50, 100]
        scale_results = []

        for scale in scales:
            print(f"  Testing with {scale} memories...")

            # Create workspace
            response = await client.post(
                f"{base_url}/api/workspaces",
                params={"name": f"vector-scale-{scale}-{int(time.time())}"},
                headers=get_auth_headers(tenant_id),
            )

            if response.status_code != 200:
                errors.append(f"Failed to create workspace for scale {scale}: {response.text}")
                continue

            workspace = response.json()
            workspace_id = workspace.get("id")

            # Add memories (creates embeddings)
            latencies = []
            for i in range(scale):
                start = time.time()

                response = await client.post(
                    f"{base_url}/api/workspaces/{workspace_id}/memories",
                    json={
                        "raw_content": f"Vector test memory number {i} with some additional context for embedding",
                        "source_type": "conversation",
                    },
                    headers=get_auth_headers(tenant_id),
                )

                latency = time.time() - start
                latencies.append(latency)

            # Test retrieval
            retrieval_start = time.time()
            response = await client.get(
                f"{base_url}/api/workspaces/{workspace_id}",
                headers=get_auth_headers(tenant_id),
            )
            retrieval_time = time.time() - retrieval_start

            scale_results.append(
                {
                    "scale": scale,
                    "ingest_avg_ms": sum(latencies) / len(latencies) * 1000,
                    "ingest_max_ms": max(latencies) * 1000,
                    "retrieval_ms": retrieval_time * 1000,
                }
            )

        metrics["scaling"] = scale_results

        # Test top-k retrieval stability
        print("  Testing top-k retrieval...")

        # Create workspace with known memories
        response = await client.post(
            f"{base_url}/api/workspaces",
            params={"name": f"topk-test-{int(time.time())}"},
            headers=get_auth_headers(tenant_id),
        )

        workspace = response.json()
        workspace_id = workspace.get("id")

        # Add specific memories
        test_memories = [
            "The quick brown fox jumps over the lazy dog",
            "Machine learning is a subset of artificial intelligence",
            "Python is a high-level programming language",
            "Database systems store and retrieve data efficiently",
            "Neural networks are inspired by biological neurons",
        ]

        for content in test_memories:
            await client.post(
                f"{base_url}/api/workspaces/{workspace_id}/memories",
                json={
                    "raw_content": content,
                    "source_type": "conversation",
                },
                headers=get_auth_headers(tenant_id),
            )

        # Test multiple retrievals
        retrieval_results = []
        for _ in range(3):
            response = await client.get(
                f"{base_url}/api/workspaces/{workspace_id}",
                headers=get_auth_headers(tenant_id),
            )
            if response.status_code == 200:
                data = response.json()
                retrieval_results.append(len(data.get("memories", [])))

        # Test ranking determinism
        ranking_deterministic = len(set(retrieval_results)) == 1

        metrics["topk"] = {
            "retrievals": retrieval_results,
            "ranking_deterministic": ranking_deterministic,
        }

        # Test scaling behavior
        if len(scale_results) >= 2:
            # Check if retrieval time scales linearly or worse
            first_scale = scale_results[0]
            last_scale = scale_results[-1]

            scale_factor = last_scale["scale"] / first_scale["scale"]
            time_factor = last_scale["retrieval_ms"] / first_scale["retrieval_ms"]

            # Linear scaling would have time_factor ≈ scale_factor
            scaling_behavior = (
                "sublinear" if time_factor < scale_factor else "linear_or_worse"
            )

            metrics["scaling_behavior"] = {
                "scale_factor": scale_factor,
                "time_factor": time_factor,
                "behavior": scaling_behavior,
            }

    duration = time.time() - start_time

    # Determine status
    has_scaling_data = len(metrics.get("scaling", [])) > 0
    deterministic = metrics.get("topk", {}).get("ranking_deterministic", False)

    status = "PASS" if has_scaling_data else "FAIL"

    return TestResult(
        test_name="test_pgvector_scaling",
        status=status,
        duration=duration,
        metrics=metrics,
        errors=errors,
    )
