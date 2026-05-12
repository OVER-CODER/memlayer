"""Phase 9 — Runtime Deployment & Multi-Tenant Workspace Infrastructure.

Deployable cognition runtime with persistence, tenancy, sessions,
snapshots, recovery, and deployment configuration.
"""

from .deployment_config import (
    DeploymentConfigurationManager,
    DeploymentConfiguration,
    DeploymentMode,
    PersistenceConfig,
    RuntimeConfig,
    TenantConfig,
)

from .workspace_persistence import (
    WorkspacePersistenceManager,
    PersistedWorkspace,
)

from .tenant_manager import (
    TenantWorkspaceManager,
    Tenant,
)

from .snapshot_engine import (
    WorkspaceSnapshotEngine,
    WorkspaceCheckpoint,
    SnapshotComparisonResult,
)

from .session_manager import (
    RuntimeSessionManager,
    RuntimeSession,
    SessionStatus,
)

from .recovery_manager import (
    RuntimeRecoveryManager,
    RecoveryResult,
)

__all__ = [
    # Config
    "DeploymentConfigurationManager", "DeploymentConfiguration",
    "DeploymentMode", "PersistenceConfig", "RuntimeConfig", "TenantConfig",
    # Persistence
    "WorkspacePersistenceManager", "PersistedWorkspace",
    # Tenancy
    "TenantWorkspaceManager", "Tenant",
    # Snapshots
    "WorkspaceSnapshotEngine", "WorkspaceCheckpoint", "SnapshotComparisonResult",
    # Sessions
    "RuntimeSessionManager", "RuntimeSession", "SessionStatus",
    # Recovery
    "RuntimeRecoveryManager", "RecoveryResult",
]
