"""
RBAC Definitions for MemLayer Security.
Defines roles and their associated permissions.
"""

from enum import Enum
from typing import List, Set, Dict

class Permission(str, Enum):
    WORKSPACE_READ = "workspace:read"
    WORKSPACE_WRITE = "workspace:write"
    REPLAY_ACCESS = "replay:access"
    GOVERNANCE_ACCESS = "governance:access"
    SNAPSHOT_RESTORE = "snapshot:restore"
    TELEMETRY_ACCESS = "telemetry:access"
    LINEAGE_ACCESS = "lineage:access"
    COORDINATION_CONTROL = "coordination:control"
    PLATFORM_ADMIN = "platform:admin"

class Role(str, Enum):
    PLATFORM_ADMIN = "platform_admin"
    TENANT_ADMIN = "tenant_admin"
    OPERATOR = "operator"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    REPLAY_AUDITOR = "replay_auditor"

ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.PLATFORM_ADMIN: {p for p in Permission},
    Role.TENANT_ADMIN: {
        Permission.WORKSPACE_READ, Permission.WORKSPACE_WRITE,
        Permission.REPLAY_ACCESS, Permission.GOVERNANCE_ACCESS,
        Permission.SNAPSHOT_RESTORE, Permission.TELEMETRY_ACCESS,
        Permission.LINEAGE_ACCESS, Permission.COORDINATION_CONTROL
    },
    Role.OPERATOR: {
        Permission.WORKSPACE_READ, Permission.REPLAY_ACCESS,
        Permission.GOVERNANCE_ACCESS, Permission.TELEMETRY_ACCESS,
        Permission.LINEAGE_ACCESS
    },
    Role.DEVELOPER: {
        Permission.WORKSPACE_READ, Permission.WORKSPACE_WRITE,
        Permission.REPLAY_ACCESS, Permission.LINEAGE_ACCESS
    },
    Role.VIEWER: {
        Permission.WORKSPACE_READ, Permission.GOVERNANCE_ACCESS
    },
    Role.REPLAY_AUDITOR: {
        Permission.REPLAY_ACCESS, Permission.GOVERNANCE_ACCESS,
        Permission.LINEAGE_ACCESS
    }
}
