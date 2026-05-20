"""
Test Replay Integrity - Phase D1.5
Validates replay determinism with 1.0 fidelity requirement.
"""

import asyncio
import httpx
import time
import json
import hashlib
from typing import Dict, Any, List
from datetime import datetime

from helpers import TestResult, get_auth_headers


def compute_canonical_hash(data: Dict) -> str:
    """Compute deterministic hash of workspace state."""
    # Sort keys for deterministic serialization
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


async def test_replay_integrity(base_url: str) -> TestResult:
    """
    Test replay determinism validation.
    Validates:
    - replay fidelity = 1.0
    - canonical serialization stability
    - integrity hash consistency
    """
    start_time = time.time()
    errors: List[str] = []
    metrics: Dict[str, Any] = {}
    tenant_id = "replay-test-tenant"

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Create workspace with known state
        print("  Creating test workspace...")

        response = await client.post(
            f"{base_url}/api/workspaces",
            params={
                "name": f"replay-test-{int(time.time())}",
                "description": "Replay determinism test",
            },
            headers=get_auth_headers(tenant_id),
        )

        if response.status_code != 200:
            errors.append(f"Failed to create workspace: {response.status_code} {response.text}")
            return TestResult(
                test_name="test_replay_integrity",
                status="ERROR",
                duration=time.time() - start_time,
                metrics={},
                errors=errors,
            )

        workspace = response.json()
        workspace_id = workspace.get("id")

        # Ingest known conversation sequence
        test_messages = [
            "First message in the conversation",
            "Second message builds on first",
            "Third message continues the thread",
            "Fourth message adds more context",
            "Fifth message concludes the initial topic",
        ]

        print(f"  Ingesting {len(test_messages)} messages...")

        for msg in test_messages:
            await client.post(
                f"{base_url}/api/workspaces/{workspace_id}/memories",
                json={
                    "raw_content": msg,
                    "source_type": "conversation",
                },
                headers=get_auth_headers(tenant_id),
            )

        # Generate first replay trace
        print("  Generating initial replay trace...")

        response1 = await client.get(
            f"{base_url}/api/workspaces/{workspace_id}",
            headers=get_auth_headers(tenant_id),
        )
        state1 = response1.json() if response1.status_code == 200 else {}
        hash1 = compute_canonical_hash(state1)

        # Generate second replay trace (should be identical)
        print("  Generating second replay trace...")

        response2 = await client.get(
            f"{base_url}/api/workspaces/{workspace_id}",
            headers=get_auth_headers(tenant_id),
        )
        state2 = response2.json() if response2.status_code == 200 else {}
        hash2 = compute_canonical_hash(state2)

        # Generate third replay trace
        response3 = await client.get(
            f"{base_url}/api/workspaces/{workspace_id}",
            headers=get_auth_headers(tenant_id),
        )
        state3 = response3.json() if response3.status_code == 200 else {}
        hash3 = compute_canonical_hash(state3)

        # Compute replay fidelity
        fidelity = (
            1.0
            if hash1 == hash2 == hash3
            else sum([hash1 == hash2, hash2 == hash3, hash1 == hash3]) / 3
        )

        metrics["replay_traces"] = {
            "hash_1": hash1[:16],
            "hash_2": hash2[:16],
            "hash_3": hash3[:16],
            "fidelity": fidelity,
            "is_deterministic": fidelity == 1.0,
        }

        # Test cross-session replay
        print("  Testing cross-session replay...")

        # Simulate new session by fetching workspace again
        response_new = await client.get(
            f"{base_url}/api/workspaces/{workspace_id}",
            headers=get_auth_headers(tenant_id),
        )
        state_new = response_new.json() if response_new.status_code == 200 else {}
        hash_new = compute_canonical_hash(state_new)

        cross_session_deterministic = hash_new == hash1

        metrics["cross_session"] = {
            "hash_match": hash_new == hash1,
            "is_deterministic": cross_session_deterministic,
        }

        # Test content retrieval consistency
        print("  Testing content retrieval consistency...")

        retrieval_hashes = []
        for _ in range(3):
            response = await client.get(
                f"{base_url}/api/workspaces/{workspace_id}",
                headers=get_auth_headers(tenant_id),
            )
            data = response.json() if response.status_code == 200 else {}
            retrieval_hashes.append(compute_canonical_hash(data))

        retrieval_deterministic = len(set(retrieval_hashes)) == 1

        metrics["retrieval"] = {
            "consistent": retrieval_deterministic,
            "unique_hashes": len(set(retrieval_hashes)),
        }

    duration = time.time() - start_time

    # Determine status - must have 1.0 fidelity
    fidelity = metrics.get("replay_traces", {}).get("fidelity", 0)
    is_deterministic = metrics.get("replay_traces", {}).get("is_deterministic", False)

    status = "PASS" if is_deterministic and cross_session_deterministic else "FAIL"

    if not is_deterministic:
        errors.append(f"Replay fidelity is {fidelity}, expected 1.0")

    return TestResult(
        test_name="test_replay_integrity",
        status=status,
        duration=duration,
        metrics=metrics,
        errors=errors,
    )
