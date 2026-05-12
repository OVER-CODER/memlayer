"""
Test Tenant Isolation - Phase D1.5
Validates zero cross-tenant data leakage.
"""

import asyncio
import httpx
import time
import json
from typing import Dict, Any, List
from datetime import datetime

from helpers import TestResult


async def test_tenant_isolation(base_url: str) -> TestResult:
    """
    Test tenant isolation.
    Validates:
    - No cross-tenant data leakage
    - Redis cache isolation
    - SQL query tenant filtering
    - Object storage path isolation
    """
    start_time = time.time()
    errors: List[str] = []
    metrics: Dict[str, Any] = {}

    tenant_ids = ["tenant-alpha", "tenant-beta", "tenant-gamma"]

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Create workspaces for each tenant
        print("  Creating isolated workspaces per tenant...")

        tenant_workspaces = {}

        for tenant_id in tenant_ids:
            response = await client.post(
            headers=get_auth_headers(),
                f"{base_url}/api/workspaces",
                params={
                    "name": f"workspace-{tenant_id}-{int(time.time())}",
                    "description": f"Exclusive workspace for {tenant_id}",
                },
                headers={"X-Tenant-ID": tenant_id},
            )

            if response.status_code == 200:
                workspace = response.json()
                tenant_workspaces[tenant_id] = workspace

        # Add tenant-specific data
        print("  Adding tenant-specific data...")

        for tenant_id, workspace in tenant_workspaces.items():
            ws_id = workspace.get("id")

            # Add memories unique to this tenant
            for i in range(3):
                await client.post(
                    f"{base_url}/api/memories",
                    params={
                        "workspace_id": ws_id,
                        "content": f"CONFIDENTIAL {tenant_id} data {i}",
                        "memory_type": "conversation",
                    },
                    headers={"X-Tenant-ID": tenant_id},
                )

        # Test 1: Cross-tenant workspace access
        print("  Testing cross-tenant workspace access...")

        cross_tenant_leaks = []

        for tenant_id, workspace in tenant_workspaces.items():
            ws_id = workspace.get("id")

            # Try to access with different tenant
            for other_tenant in tenant_ids:
                if other_tenant != tenant_id:
                    response = await client.get(
                        f"{base_url}/api/workspaces/{ws_id}",
                        headers={"X-Tenant-ID": other_tenant},
                    )

                    # Should either be rejected or show filtered data
                    if response.status_code == 200:
                        data = response.json()
                        memories = data.get("memories", [])

                        # Check if we can see other tenant's data
                        for memory in memories:
                            content = memory.get("content", "")
                            if f"CONFIDENTIAL {other_tenant}" in content:
                                cross_tenant_leaks.append(
                                    {
                                        "requested_tenant": other_tenant,
                                        "accessed_workspace": ws_id,
                                        "leaked_content": content[:50],
                                    }
                                )

        metrics["workspace_isolation"] = {
            "total_attempts": len(tenant_ids) * (len(tenant_ids) - 1),
            "leaks_found": len(cross_tenant_leaks),
        }

        if cross_tenant_leaks:
            errors.append(
                f"Cross-tenant workspace leak detected: {len(cross_tenant_leaks)}"
            )

        # Test 2: Redis cache isolation
        print("  Testing Redis cache isolation...")

        # Create separate workspaces and verify cache doesn't leak
        for tenant_id in tenant_ids:
            response = await client.post(
            headers=get_auth_headers(),
                f"{base_url}/api/workspaces",
                params={"name": f"cache-test-{tenant_id}"},
                headers={"X-Tenant-ID": tenant_id},
            )

        # Check if workspaces list shows only tenant's workspaces
        for tenant_id in tenant_ids:
            response = await client.get(
                f"{base_url}/api/workspaces", headers={"X-Tenant-ID": tenant_id}
            )

            workspaces = response.json() if response.status_code == 200 else []

            # Count workspaces that belong to this tenant
            tenant_workspace_count = len(
                [ws for ws in workspaces if ws.get("tenant_id") == tenant_id]
            )

            # Verify only tenant's workspaces are visible
            all_tenants_visible = any(
                ws.get("tenant_id") != tenant_id for ws in workspaces
            )

            if all_tenants_visible and len(workspaces) > 1:
                errors.append(
                    f"Redis cache leak: {tenant_id} can see other tenants' workspaces"
                )

        metrics["cache_isolation"] = {"verified": len(errors) == 0}

        # Test 3: SQL query tenant filtering
        print("  Testing SQL query filtering...")

        # Try direct workspace ID access
        for tenant_id, workspace in tenant_workspaces.items():
            ws_id = workspace.get("id")

            # Access with different tenant should fail or filter
            for other_tenant in tenant_ids:
                if other_tenant != tenant_id:
                    response = await client.get(
                        f"{base_url}/api/workspaces/{ws_id}",
                        headers={"X-Tenant-ID": other_tenant},
                    )

                    # Should be 403 Forbidden or 404 Not Found, not 200 with data
                    if response.status_code == 200:
                        data = response.json()
                        has_data = len(data.get("memories", [])) > 0

                        if has_data:
                            errors.append(
                                f"SQL filter leak: {other_tenant} accessed {tenant_id}'s data"
                            )

        metrics["sql_filtering"] = {"leaks": len([e for e in errors if "SQL" in e])}

        # Test 4: Object storage path isolation
        print("  Testing object storage isolation...")

        # Attempt to access with path traversal
        malicious_paths = ["../other-tenant/", "/etc/passwd", "..%2Fother-tenant"]

        path_leaks = []
        for path in malicious_paths:
            response = await client.get(
                f"{base_url}/api/workspaces/{path}",
                headers={"X-Tenant-ID": "tenant-alpha"},
            )

            if response.status_code == 200:
                path_leaks.append(path)

        metrics["storage_isolation"] = {
            "path_traversal_attempts": len(malicious_paths),
            "leaks": len(path_leaks),
        }

    duration = time.time() - start_time

    # Determine status - must have ZERO leaks
    total_leaks = len(cross_tenant_leaks) + len(
        [e for e in errors if "leak" in e.lower()]
    )

    status = "PASS" if total_leaks == 0 else "FAIL"

    if total_leaks > 0:
        errors.append(f"Total tenant isolation leaks: {total_leaks}")

    return TestResult(
        test_name="test_tenant_isolation",
        status=status,
        duration=duration,
        metrics=metrics,
        errors=errors,
    )
