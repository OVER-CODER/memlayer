"""Phase 8 — MemLayer SDK & Runtime APIs.

External integration layer for the MemLayer cognition runtime.
"""

from .memlayer_sdk import MemLayerSDK
from .workspace_api import WorkspaceAPI, WorkspaceConfig, WorkspaceSnapshot
from .view_api import ViewAPI, ViewResult, ViewComparisonResult
from .coordination_api import CoordinationAPI, CoordinationRequest, CoordinationSummary
from .replay_api import ReplayAPI, ReplayResult, ReplayComparisonResult
from .telemetry_api import TelemetryAPI
from .provider_adapters import ProviderAdapter, ProviderCapabilities, PROVIDER_REGISTRY

__all__ = [
    "MemLayerSDK",
    "WorkspaceAPI", "WorkspaceConfig", "WorkspaceSnapshot",
    "ViewAPI", "ViewResult", "ViewComparisonResult",
    "CoordinationAPI", "CoordinationRequest", "CoordinationSummary",
    "ReplayAPI", "ReplayResult", "ReplayComparisonResult",
    "TelemetryAPI",
    "ProviderAdapter", "ProviderCapabilities", "PROVIDER_REGISTRY",
]
