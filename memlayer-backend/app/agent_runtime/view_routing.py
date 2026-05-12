"""View Routing Engine for Phase 7 Shared Agent Runtime.

Assigns semantic views to agents, optimizes provider/view combinations,
preserves projection specialization, and tracks projection reuse efficiency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import hashlib

from app.view_engine.definitions import ViewType
from app.view_engine.compiler import CompiledSemanticView, WorkspaceSemanticState
from app.agent_runtime.agents import AgentType, AGENT_VIEW_MAP, AGENT_CAPABILITIES


@dataclass
class RoutingDecision:
    """Record of a view routing decision."""

    agent_id: str
    agent_type: AgentType
    assigned_view_type: ViewType
    assigned_provider: str
    routing_reason: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    projection_reused: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "assigned_view_type": self.assigned_view_type.value,
            "assigned_provider": self.assigned_provider,
            "routing_reason": self.routing_reason,
            "timestamp": self.timestamp.isoformat(),
            "projection_reused": self.projection_reused,
        }


@dataclass
class RoutingMetrics:
    """Metrics for view routing quality."""

    total_routing_decisions: int = 0
    projection_reuse_count: int = 0
    projection_reuse_ratio: float = 0.0
    provider_distribution: Dict[str, int] = field(default_factory=dict)
    view_distribution: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_routing_decisions": self.total_routing_decisions,
            "projection_reuse_count": self.projection_reuse_count,
            "projection_reuse_ratio": self.projection_reuse_ratio,
            "provider_distribution": self.provider_distribution,
            "view_distribution": self.view_distribution,
        }


class ViewRoutingEngine:
    """Routes compiled semantic views to agents.

    Routing strategy:
    - Each agent type has a canonical view mapping (AGENT_VIEW_MAP)
    - Provider selection respects agent capability preferences
    - Projections are reused when possible (same state + provider)
    - Routing decisions are tracked for coordination telemetry
    """

    def __init__(self):
        self._routing_log: List[RoutingDecision] = []
        self._active_projections: Dict[str, str] = {}  # projection_key -> checksum

    def resolve_view_type(self, agent_type: AgentType) -> ViewType:
        """Resolve canonical view type for an agent type."""
        view_name = AGENT_VIEW_MAP[agent_type]
        return ViewType(view_name)

    def resolve_provider(
        self,
        agent_type: AgentType,
        semantic_state: WorkspaceSemanticState,
        preferred_provider: Optional[str] = None,
    ) -> str:
        """Resolve optimal provider for an agent type.

        Priority: explicit preference > agent capability profile > workspace default.
        """
        if preferred_provider:
            return preferred_provider

        caps = AGENT_CAPABILITIES.get(agent_type)
        if caps and caps.preferred_providers:
            # Use the first preferred provider that exists
            return caps.preferred_providers[0]

        return semantic_state.provider

    def route(
        self,
        agent_id: str,
        agent_type: AgentType,
        semantic_state: WorkspaceSemanticState,
        available_views: Dict[str, CompiledSemanticView],
        preferred_provider: Optional[str] = None,
    ) -> Tuple[ViewType, str, bool]:
        """Route an agent to a view and provider.

        Returns:
            (view_type, provider, projection_reused)
        """
        view_type = self.resolve_view_type(agent_type)
        provider = self.resolve_provider(agent_type, semantic_state, preferred_provider)

        # Check if this projection was already generated
        projection_key = f"{semantic_state.workspace_id}|{semantic_state.state_checksum()}|{view_type.value}|{provider}"
        view = available_views.get(view_type.value)
        reused = False
        if view:
            current_checksum = view.projection.projection_checksum
            if projection_key in self._active_projections:
                reused = self._active_projections[projection_key] == current_checksum
            self._active_projections[projection_key] = current_checksum

        decision = RoutingDecision(
            agent_id=agent_id,
            agent_type=agent_type,
            assigned_view_type=view_type,
            assigned_provider=provider,
            routing_reason=f"canonical:{agent_type.value}→{view_type.value}",
            projection_reused=reused,
        )
        self._routing_log.append(decision)

        return view_type, provider, reused

    def get_routing_metrics(self) -> RoutingMetrics:
        """Calculate routing quality metrics."""
        if not self._routing_log:
            return RoutingMetrics()

        total = len(self._routing_log)
        reused = sum(1 for d in self._routing_log if d.projection_reused)

        provider_dist: Dict[str, int] = {}
        view_dist: Dict[str, int] = {}
        for d in self._routing_log:
            provider_dist[d.assigned_provider] = provider_dist.get(d.assigned_provider, 0) + 1
            view_dist[d.assigned_view_type.value] = view_dist.get(d.assigned_view_type.value, 0) + 1

        return RoutingMetrics(
            total_routing_decisions=total,
            projection_reuse_count=reused,
            projection_reuse_ratio=reused / total if total > 0 else 0.0,
            provider_distribution=provider_dist,
            view_distribution=view_dist,
        )

    def get_routing_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        return [d.to_dict() for d in self._routing_log[-limit:]]
