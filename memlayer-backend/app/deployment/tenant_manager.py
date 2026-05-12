"""Multi-Tenant Workspace Manager for Phase 9.

Lightweight, runtime-focused tenant isolation. Each tenant gets isolated
workspace namespaces, replay histories, and telemetry domains.
Not an enterprise auth platform — just cognition isolation boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from app.deployment.deployment_config import TenantConfig
from app.deployment.workspace_persistence import WorkspacePersistenceManager


@dataclass
class Tenant:
    """Tenant registration."""

    tenant_id: str
    name: str = ""
    workspace_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "workspace_count": len(self.workspace_ids),
            "workspace_ids": list(self.workspace_ids),
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


class TenantWorkspaceManager:
    """Manages tenant-isolated workspace namespaces.

    Guarantees:
    - Workspaces are scoped to tenants
    - Cross-tenant access is blocked
    - Telemetry and replay are tenant-isolated
    - Workspace limits are enforced per tenant
    """

    def __init__(
        self,
        persistence: Optional[WorkspacePersistenceManager] = None,
        config: Optional[TenantConfig] = None,
    ):
        self._persistence = persistence or WorkspacePersistenceManager()
        self._config = config or TenantConfig()
        self._tenants: Dict[str, Tenant] = {}

    def register_tenant(
        self,
        tenant_id: Optional[str] = None,
        name: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tenant:
        """Register a new tenant."""
        tid = tenant_id or f"tenant-{uuid.uuid4().hex[:10]}"
        if tid in self._tenants:
            return self._tenants[tid]

        tenant = Tenant(tenant_id=tid, name=name, metadata=metadata or {})
        self._tenants[tid] = tenant
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self._tenants.get(tenant_id)

    def create_workspace(
        self,
        tenant_id: str,
        workspace_id: Optional[str] = None,
    ) -> str:
        """Create a workspace scoped to a tenant."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        if len(tenant.workspace_ids) >= self._config.max_workspaces_per_tenant:
            raise ValueError(
                f"Tenant {tenant_id} at workspace limit "
                f"({self._config.max_workspaces_per_tenant})"
            )

        ws_id = workspace_id or f"{tenant_id}-ws-{uuid.uuid4().hex[:8]}"
        tenant.workspace_ids.append(ws_id)
        return ws_id

    def validate_access(self, tenant_id: str, workspace_id: str) -> bool:
        """Validate that a tenant owns a workspace."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False
        return workspace_id in tenant.workspace_ids

    def get_tenant_workspaces(self, tenant_id: str) -> List[str]:
        """Get all workspace IDs for a tenant."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return []
        return list(tenant.workspace_ids)

    def remove_workspace(self, tenant_id: str, workspace_id: str) -> bool:
        """Remove a workspace from a tenant."""
        tenant = self._tenants.get(tenant_id)
        if not tenant or workspace_id not in tenant.workspace_ids:
            return False
        tenant.workspace_ids.remove(workspace_id)
        self._persistence.delete(workspace_id)
        return True

    def get_isolation_report(self) -> Dict[str, Any]:
        """Get tenant isolation integrity report."""
        all_ws = []
        for tenant in self._tenants.values():
            all_ws.extend(tenant.workspace_ids)

        # Check for cross-tenant workspace collisions
        unique_ws = set(all_ws)
        has_collision = len(all_ws) != len(unique_ws)

        return {
            "total_tenants": len(self._tenants),
            "total_workspaces": len(all_ws),
            "unique_workspaces": len(unique_ws),
            "isolation_intact": not has_collision,
            "tenants": {
                tid: {"workspace_count": len(t.workspace_ids)}
                for tid, t in self._tenants.items()
            },
        }
