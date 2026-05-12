"""Deployment Configuration Layer for Phase 9.

Typed, minimal deployment configurations for local/hosted modes,
provider runtime configs, and persistence tuning. All configs are
deterministic and serializable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional
import json


class DeploymentMode(str, Enum):
    LOCAL = "local"
    HOSTED = "hosted"
    SELF_HOSTED = "self_hosted"


@dataclass
class PersistenceConfig:
    """Persistence layer configuration."""

    storage_dir: str = ".memlayer/data"
    snapshot_dir: str = ".memlayer/snapshots"
    max_snapshots_per_workspace: int = 100
    auto_persist: bool = True
    compression: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "storage_dir": self.storage_dir,
            "snapshot_dir": self.snapshot_dir,
            "max_snapshots_per_workspace": self.max_snapshots_per_workspace,
            "auto_persist": self.auto_persist,
            "compression": self.compression,
        }


@dataclass
class RuntimeConfig:
    """Runtime tuning configuration."""

    default_provider: str = "claude"
    default_token_budget: int = 4000
    max_coordination_depth: int = 4
    max_agents_per_run: int = 8
    session_timeout_seconds: int = 3600
    replay_history_limit: int = 1000

    def to_dict(self) -> Dict[str, Any]:
        return {
            "default_provider": self.default_provider,
            "default_token_budget": self.default_token_budget,
            "max_coordination_depth": self.max_coordination_depth,
            "max_agents_per_run": self.max_agents_per_run,
            "session_timeout_seconds": self.session_timeout_seconds,
            "replay_history_limit": self.replay_history_limit,
        }


@dataclass
class TenantConfig:
    """Multi-tenant isolation configuration."""

    max_workspaces_per_tenant: int = 50
    max_memories_per_workspace: int = 10000
    isolated_telemetry: bool = True
    isolated_replay: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_workspaces_per_tenant": self.max_workspaces_per_tenant,
            "max_memories_per_workspace": self.max_memories_per_workspace,
            "isolated_telemetry": self.isolated_telemetry,
            "isolated_replay": self.isolated_replay,
        }


@dataclass
class DeploymentConfiguration:
    """Complete deployment configuration."""

    mode: DeploymentMode = DeploymentMode.LOCAL
    persistence: PersistenceConfig = field(default_factory=PersistenceConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    tenant: TenantConfig = field(default_factory=TenantConfig)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "persistence": self.persistence.to_dict(),
            "runtime": self.runtime.to_dict(),
            "tenant": self.tenant.to_dict(),
            "metadata": self.metadata,
        }


class DeploymentConfigurationManager:
    """Manages deployment configurations.

    Provides typed, validated configs for local/hosted/self-hosted modes.
    All configurations are deterministic and serializable.
    """

    def __init__(self, config: Optional[DeploymentConfiguration] = None):
        self._config = config or DeploymentConfiguration()

    @property
    def config(self) -> DeploymentConfiguration:
        return self._config

    @staticmethod
    def local(storage_dir: str = ".memlayer/data", **overrides) -> DeploymentConfigurationManager:
        """Create a local deployment config."""
        cfg = DeploymentConfiguration(
            mode=DeploymentMode.LOCAL,
            persistence=PersistenceConfig(storage_dir=storage_dir),
        )
        return DeploymentConfigurationManager(cfg)

    @staticmethod
    def hosted(**overrides) -> DeploymentConfigurationManager:
        """Create a hosted deployment config."""
        cfg = DeploymentConfiguration(
            mode=DeploymentMode.HOSTED,
            persistence=PersistenceConfig(auto_persist=True, compression=True),
            runtime=RuntimeConfig(session_timeout_seconds=7200),
        )
        return DeploymentConfigurationManager(cfg)

    @staticmethod
    def self_hosted(storage_dir: str = "/data/memlayer", **overrides) -> DeploymentConfigurationManager:
        """Create a self-hosted deployment config."""
        cfg = DeploymentConfiguration(
            mode=DeploymentMode.SELF_HOSTED,
            persistence=PersistenceConfig(storage_dir=storage_dir, compression=True),
            runtime=RuntimeConfig(replay_history_limit=5000),
        )
        return DeploymentConfigurationManager(cfg)

    def export_config(self, output_file: str) -> str:
        with open(output_file, "w") as f:
            json.dump(self._config.to_dict(), f, indent=2)
        return output_file

    def validate(self) -> Dict[str, Any]:
        """Validate the current configuration."""
        issues = []
        if self._config.runtime.default_token_budget < 100:
            issues.append("token_budget too low")
        if self._config.tenant.max_workspaces_per_tenant < 1:
            issues.append("max_workspaces must be >= 1")
        return {"valid": len(issues) == 0, "issues": issues}
