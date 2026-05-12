"""Phase 7 — Shared Agent Runtime.

Coordinated semantic runtime consumers that share compiled cognition.
All agents consume the SAME semantic projections produced by the
cognition substrate. No agent independently rebuilds context.
"""

from .agents import (
    AgentType,
    AgentCapabilities,
    AgentExecutionResult,
    AGENT_CAPABILITIES,
    AGENT_VIEW_MAP,
)

from .context_bus import (
    SharedContextBus,
    ContextAccessRecord,
    ContextReuseMetrics,
)

from .agent_registry import (
    AgentStateRegistry,
    AgentRegistration,
    CoordinationEvent,
)

from .view_routing import (
    ViewRoutingEngine,
    RoutingDecision,
    RoutingMetrics,
)

from .delegation import (
    DelegationRuntime,
    DelegationRequest,
    DelegationResult,
    DelegationChain,
)

from .coordination_telemetry import (
    CoordinationTelemetryService,
    CoordinationTrace,
    CoordinationDiagnostics,
)

from .runtime_kernel import (
    SharedAgentRuntime,
    CoordinatedExecutionPlan,
    CoordinatedExecutionReport,
)

# Phase 7.5 — Coordination Intelligence
from .coordination_policy import (
    CoordinationPolicyEngine,
    CoordinationPolicy,
    PolicyDecision,
    PolicyType,
    PolicyEffectivenessReport,
)

from .adaptive_delegation import (
    AdaptiveDelegationEngine,
    AdaptiveDelegationResult,
    DelegationCandidate,
)

from .provider_routing import (
    ProviderRoutingIntelligence,
    ProviderRoutingResult,
)

from .projection_refresh import (
    ProjectionRefreshManager,
    RefreshDecision,
    ProjectionFreshnessRecord,
)

from .budget_optimizer import (
    CoordinationBudgetOptimizer,
    CoordinationBudgetPlan,
    BudgetAllocation,
)

__all__ = [
    # Agent Types
    "AgentType",
    "AgentCapabilities",
    "AgentExecutionResult",
    "AGENT_CAPABILITIES",
    "AGENT_VIEW_MAP",
    # Context Bus
    "SharedContextBus",
    "ContextAccessRecord",
    "ContextReuseMetrics",
    # Agent Registry
    "AgentStateRegistry",
    "AgentRegistration",
    "CoordinationEvent",
    # View Routing
    "ViewRoutingEngine",
    "RoutingDecision",
    "RoutingMetrics",
    # Delegation
    "DelegationRuntime",
    "DelegationRequest",
    "DelegationResult",
    "DelegationChain",
    # Coordination Telemetry
    "CoordinationTelemetryService",
    "CoordinationTrace",
    "CoordinationDiagnostics",
    # Runtime Kernel
    "SharedAgentRuntime",
    "CoordinatedExecutionPlan",
    "CoordinatedExecutionReport",
    # Phase 7.5 — Coordination Intelligence
    "CoordinationPolicyEngine",
    "CoordinationPolicy",
    "PolicyDecision",
    "PolicyType",
    "PolicyEffectivenessReport",
    "AdaptiveDelegationEngine",
    "AdaptiveDelegationResult",
    "DelegationCandidate",
    "ProviderRoutingIntelligence",
    "ProviderRoutingResult",
    "ProjectionRefreshManager",
    "RefreshDecision",
    "ProjectionFreshnessRecord",
    "CoordinationBudgetOptimizer",
    "CoordinationBudgetPlan",
    "BudgetAllocation",
]
