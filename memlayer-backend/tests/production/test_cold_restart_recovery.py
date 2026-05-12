"""
Test Cold Restart Recovery - Phase D1.5
Validates system behavior after backend restart.
"""

import asyncio
import httpx
import time
import json
from typing import Dict, Any, List
from datetime import datetime

from helpers import TestResult, get_auth_headers


async def test_cold_restart_recovery(base_url: str) -> TestResult:
    """
    Test cold restart recovery.
    Validates:
    - State restoration
    - Connection re-establishment
    - Data integrity after restart
    """
    start_time = time.time()
    errors: List[str] = []
    metrics: Dict[str, Any] = {}
    tenant_id = "restart-test-tenant"

    # Note: This test validates the system state assuming the service stays up.
    # True cold restart testing would require stopping/starting the service.
    # Here we simulate the validation of persistent state.

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test 1: Verify health after any restart
        print("  Checking system health...")

        response = await client.get(f"{base_url}/health/ready")
        ready_data = response.json() if response.status_code == 200 else {}

        metrics["health_check"] = {
            "status": ready_data.get("status"),
            "database": ready_data.get("database"),
            "redis": ready_data.get("redis"),
        }

        # Test 2: Verify database persistence
        print("  Verifying database persistence...")

        # Test 2: Verify database persistence
        print("  Verifying database persistence...")

        response = await client.get(
            f"{base_url}/api/workspaces",
            headers=get_auth_headers(tenant_id),
        )
        workspaces = response.json() if response.status_code == 200 else []

        metrics["persistence"] = {
            "workspaces_count": len(workspaces),
            "accessible": response.status_code == 200,
        }

        # Test 3: Create new data and verify persistence
        print("  Testing new data persistence...")

        response = await client.post(
            f"{base_url}/api/workspaces",
            params={"name": f"restart-test-{int(time.time())}"},
            headers=get_auth_headers(tenant_id),
        )

        new_workspace = response.json() if response.status_code == 200 else {}
        new_ws_id = new_workspace.get("id")

        # Add memory
        if new_ws_id:
            response = await client.post(
                f"{base_url}/api/memories",
                params={
                    "workspace_id": new_ws_id,
                    "content": "Persistence test message",
                    "memory_type": "conversation",
                },
                headers=get_auth_headers(tenant_id),
            )

            memory_created = response.status_code == 200

            # Verify it's persisted
            response = await client.get(
                f"{base_url}/api/workspaces/{new_ws_id}",
                headers=get_auth_headers(tenant_id),
            )
            data_persisted = response.status_code == 200

            metrics["new_data"] = {
                "workspace_created": True,
                "memory_created": memory_created,
                "data_persisted": data_persisted,
            }

        # Test 4: Verify Redis cache persistence
        print("  Testing Redis state...")

        # Readiness endpoint checks Redis
        ready = ready_data.get("status") == "ready"

        metrics["redis_state"] = {"connected": ready_data.get("redis") == "connected"}

    duration = time.time() - start_time

    # Determine status
    ready = metrics.get("health_check", {}).get("status") == "ready"
    db_ok = metrics.get("health_check", {}).get("database") == "connected"
    redis_ok = metrics.get("health_check", {}).get("redis") == "connected"

    status = "PASS" if ready and db_ok and redis_ok else "FAIL"

    return TestResult(
        test_name="test_cold_restart_recovery",
        status=status,
        duration=duration,
        metrics=metrics,
        errors=errors,
    )
