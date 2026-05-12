"""Provider Routing Intelligence for Phase 7.5.

Selects optimal providers per agent role based on quality history,
token pressure, projection type, and coordination context.
All routing decisions are deterministic and replayable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.agent_runtime.agents import AgentType, AGENT_CAPABILITIES
from app.agent_runtime.coordination_policy import (
    CoordinationPolicyEngine,
    PolicyDecision,
)


@dataclass
class ProviderRoutingResult:
    """Outcome of a provider routing decision."""

    agent_type: AgentType
    selected_provider: str
    provider_scores: Dict[str, float]
    policy_decision: PolicyDecision
    workspace_id: str = ""
    token_pressure: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_type": self.agent_type.value,
            "selected_provider": self.selected_provider,
            "provider_scores": self.provider_scores,
            "policy_outcome": self.policy_decision.outcome,
            "workspace_id": self.workspace_id,
            "token_pressure": self.token_pressure,
        }


class ProviderRoutingIntelligence:
    """Selects optimal providers using quality history and coordination context.

    Routing signals:
    - Historical quality per provider per agent type
    - Token pressure (prefer token-efficient providers under pressure)
    - Agent capability preferences
    - Coordination history (stability of provider across runs)

    All decisions are deterministic given the same signals.
    """

    def __init__(self, policy_engine: Optional[CoordinationPolicyEngine] = None):
        self.policy = policy_engine or CoordinationPolicyEngine()
        self._quality_history: Dict[str, Dict[str, List[float]]] = {}  # agent_type -> provider -> scores
        self._results: List[ProviderRoutingResult] = []

    def record_quality(self, agent_type: AgentType, provider: str, quality: float) -> None:
        """Record a quality observation for a provider/agent combination."""
        key = agent_type.value
        self._quality_history.setdefault(key, {}).setdefault(provider, []).append(quality)
        # Keep last 50 observations per combination
        if len(self._quality_history[key][provider]) > 50:
            self._quality_history[key][provider] = self._quality_history[key][provider][-50:]

    def select_provider(
        self,
        agent_type: AgentType,
        workspace_id: str,
        available_providers: List[str],
        token_pressure: float = 0.0,
    ) -> ProviderRoutingResult:
        """Select optimal provider for an agent type."""
        quality_avg = self._get_quality_averages(agent_type, available_providers)

        # Policy evaluation
        policy_decision = self.policy.evaluate_provider_routing(
            agent_type=agent_type,
            workspace_id=workspace_id,
            available_providers=available_providers,
            provider_quality_history=quality_avg,
            token_pressure=token_pressure,
        )

        selected = policy_decision.outcome
        if selected not in available_providers and available_providers:
            selected = available_providers[0]

        result = ProviderRoutingResult(
            agent_type=agent_type,
            selected_provider=selected,
            provider_scores=quality_avg,
            policy_decision=policy_decision,
            workspace_id=workspace_id,
            token_pressure=token_pressure,
        )
        self._results.append(result)
        return result

    def get_routing_quality(self) -> Dict[str, Any]:
        """Get provider routing quality metrics."""
        if not self._results:
            return {"message": "No routing decisions"}

        provider_counts: Dict[str, int] = {}
        for r in self._results:
            provider_counts[r.selected_provider] = provider_counts.get(r.selected_provider, 0) + 1

        return {
            "total_decisions": len(self._results),
            "provider_selection_distribution": provider_counts,
            "quality_history_depth": {
                at: {p: len(scores) for p, scores in providers.items()}
                for at, providers in self._quality_history.items()
            },
        }

    def _get_quality_averages(
        self,
        agent_type: AgentType,
        providers: List[str],
    ) -> Dict[str, float]:
        """Get average quality scores for each provider."""
        history = self._quality_history.get(agent_type.value, {})
        result: Dict[str, float] = {}
        for p in providers:
            scores = history.get(p, [])
            result[p] = sum(scores) / len(scores) if scores else 0.5  # default neutral
        return result
