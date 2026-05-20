"""
Test helper module - provides authentication and common utilities.
"""

import httpx
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Any

# JWT Token for authenticated API requests (generated with production secret key)
# Production uses the default dev secret key from config
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXIiLCJ0ZW5hbnRfaWQiOiJ0ZXN0LXRlbmFudCIsInJvbGUiOiJhZG1pbiIsImV4cCI6MjA5NDYzMzE1NCwiaWF0IjoxNzc5MjczMTU0fQ.0KwSe9CiiTQAC8txJ0-MIxVitkfoLzv_duzFdJnvHG8"


@dataclass
class TestResult:
    test_name: str
    status: str  # PASS, FAIL, SKIP, ERROR
    duration: float
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def get_auth_headers(tenant_id: str = "test-tenant") -> Dict[str, str]:
    """Get authentication headers."""
    return {"Authorization": f"Bearer {JWT_TOKEN}", "X-Tenant-ID": tenant_id}


async def create_workspace(
    client: httpx.AsyncClient,
    base_url: str,
    name: str,
    description: str = "",
    tenant_id: str = "test-tenant",
) -> Dict:
    """Create a workspace via API."""
    response = await client.post(
        f"{base_url}/api/workspaces",
        params={"name": name, "description": description},
        headers=get_auth_headers(tenant_id),
    )
    return response.json() if response.status_code == 200 else {}


async def get_workspace(
    client: httpx.AsyncClient,
    base_url: str,
    workspace_id: str,
    tenant_id: str = "test-tenant",
) -> Dict:
    """Get a workspace via API."""
    response = await client.get(
        f"{base_url}/api/workspaces/{workspace_id}", headers=get_auth_headers(tenant_id)
    )
    return response.json() if response.status_code == 200 else {}


async def list_workspaces(
    client: httpx.AsyncClient, base_url: str, tenant_id: str = "test-tenant"
) -> list:
    """List workspaces via API."""
    response = await client.get(
        f"{base_url}/api/workspaces", headers=get_auth_headers(tenant_id)
    )
    return response.json() if response.status_code == 200 else []


async def create_memory(
    client: httpx.AsyncClient,
    base_url: str,
    workspace_id: str,
    content: str,
    memory_type: str = "conversation",
    tenant_id: str = "test-tenant",
) -> Dict:
    """Create a memory via API (tenant-scoped)."""
    response = await client.post(
        f"{base_url}/api/workspaces/{workspace_id}/memories",
        json={
            "raw_content": content,
            "source_type": memory_type,
        },
        headers=get_auth_headers(tenant_id),
    )
    return response.json() if response.status_code == 200 else {}
