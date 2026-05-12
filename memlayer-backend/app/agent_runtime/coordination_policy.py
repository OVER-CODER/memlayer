"""Coordination Policy Engine for Phase 7.5.

Deterministic, replayable policy evaluation for coordination decisions.
Policies govern delegation, provider routing, token budgets, and
projection refresh. Every policy decision is traceable and benchmarkable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from app.agent_runtime.agents import AgentType, AGENT_CAPABILITIES


class PolicyType(str, Enum):
    DELEGATION = "delegation"
    PROVIDER_ROUTING = "provider_routing"
    TOKEN_BUDGET = "token_budget"
    PROJECTION_REFRESH = "projection_refresh"


@dataclass
class PolicyDecision:
    """Record of a single policy evaluation."""

    decision_id: str
    policy_type: PolicyType
    agent_type: Optional[AgentType] = None
    workspace_id: str = ""
    input_signals: Dict[str, Any] = field(default_factory=dict)
    outcome: str = ""
    rationale: str = ""
    optimization_delta: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "policy_type": self.policy_type.value,
            "agent_type": self.agent_type.value if self.agent_type else None,
            "workspace_id": self.workspace_id,
            "input_signals": self.input_signals,
            "outcome": self.outcome,
            "rationale": self.rationale,
            "optimization_delta": self.optimization_delta,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class PolicyEffectivenessReport:
    """Aggregated policy effectiveness metrics."""

    total_decisions: int = 0
    decisions_by_type: Dict[str, int] = field(default_factory=dict)
    avg_optimization_delta: float = 0.0
    positive_outcomes: int = 0
    effectiveness_ratio: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_decisions": self.total_decisions,
            "decisions_by_type": self.decisions_by_type,
            "avg_optimization_delta": self.avg_optimization_delta,
            "positive_outcomes": self.positive_outcomes,
            "effectiveness_ratio": self.effectiveness_ratio,
        }


@dataclass
class CoordinationPolicy:
    """A single coordination policy with configurable thresholds."""

    name: str
    policy_type: PolicyType
    enabled: bool = True
    # Thresholds
    token_pressure_threshold: float = 0.85
    staleness_threshold_seconds: float = 300.0
    min_semantic_continuity: float = 0.25
    max_delegation_depth: int = 4
    provider_quality_floor: float = 0.60


class CoordinationPolicyEngine:
    """Deterministic policy evaluation for coordination decisions.

    All policy decisions are:
    - Deterministic given the same inputs
    - Replayable via the decision log
    - Benchmarkable via effectiveness reports
    """

    def __init__(self, policies: Optional[List[CoordinationPolicy]] = None):
        self._policies = {p.name: p for p in (policies or self._default_policies())}
        self._decisions: List[PolicyDecision] = []
        self._counter = 0

    # -----------------------------------------------------------------
    # Policy evaluation
    # -----------------------------------------------------------------

    def evaluate_delegation(
        self,
        source_type: AgentType,
        target_type: AgentType,
        workspace_id: str,
        semantic_continuity: float = 0.0,
        delegation_depth: int = 0,
        token_pressure: float = 0.0,
    ) -> PolicyDecision:
        """Evaluate whether a delegation should proceed."""
        self._counter += 1
        policy = self._get_policy("delegation_gate")

        signals = {
            "source": source_type.value,
            "target": target_type.value,
            "semantic_continuity": semantic_continuity,
            "delegation_depth": delegation_depth,
            "token_pressure": token_pressure,
        }

        # Decision logic: deterministic rules
        if not policy.enabled:
            return self._record("allow", "policy_disabled", signals,
                                PolicyType.DELEGATION, source_type, workspace_id)

        if delegation_depth >= policy.max_delegation_depth:
            return self._record("deny", "max_depth_exceeded", signals,
                                PolicyType.DELEGATION, source_type, workspace_id, -0.1)

        if token_pressure > policy.token_pressure_threshold:
            return self._record("defer", "token_pressure_high", signals,
                                PolicyType.DELEGATION, source_type, workspace_id, -0.05)

        if semantic_continuity < policy.min_semantic_continuity and delegation_depth > 0:
            return self._record("deny", "low_semantic_continuity", signals,
                                PolicyType.DELEGATION, source_type, workspace_id, -0.15)

        return self._record("allow", "within_policy_bounds", signals,
                            PolicyType.DELEGATION, source_type, workspace_id, 0.1)

    def evaluate_provider_routing(
        self,
        agent_type: AgentType,
        workspace_id: str,
        available_providers: List[str],
        provider_quality_history: Optional[Dict[str, float]] = None,
        token_pressure: float = 0.0,
    ) -> PolicyDecision:
        """Evaluate optimal provider for an agent."""
        self._counter += 1
        policy = self._get_policy("provider_routing")
        quality_hist = provider_quality_history or {}

        signals = {
            "agent_type": agent_type.value,
            "available_providers": available_providers,
            "quality_history": quality_hist,
            "token_pressure": token_pressure,
        }

        if not available_providers:
            return self._record("none", "no_providers", signals,
                                PolicyType.PROVIDER_ROUTING, agent_type, workspace_id)

        # Filter by quality floor
        qualified = [
            p for p in available_providers
            if quality_hist.get(p, 1.0) >= policy.provider_quality_floor
        ]
        if not qualified:
            qualified = available_providers  # fallback: use all

        # Select best by quality history, deterministic tiebreak by name
        best = max(qualified, key=lambda p: (quality_hist.get(p, 0.5), p))

        delta = quality_hist.get(best, 0.5) - 0.5
        return self._record(best, f"best_qualified:{best}", signals,
                            PolicyType.PROVIDER_ROUTING, agent_type, workspace_id, delta)

    def evaluate_token_budget(
        self,
        agent_type: AgentType,
        workspace_id: str,
        base_budget: int,
        token_pressure: float = 0.0,
        agent_count: int = 1,
    ) -> PolicyDecision:
        """Evaluate token budget allocation for an agent."""
        self._counter += 1
        policy = self._get_policy("token_budget")
        caps = AGENT_CAPABILITIES.get(agent_type)
        budget_ratio = caps.max_token_budget_ratio if caps else 1.0

        signals = {
            "agent_type": agent_type.value,
            "base_budget": base_budget,
            "token_pressure": token_pressure,
            "agent_count": agent_count,
            "budget_ratio": budget_ratio,
        }

        # Under pressure: reduce proportionally
        pressure_factor = 1.0
        if token_pressure > policy.token_pressure_threshold:
            pressure_factor = max(0.6, 1.0 - (token_pressure - policy.token_pressure_threshold))

        allocated = int(base_budget * budget_ratio * pressure_factor)
        delta = (allocated - base_budget) / max(base_budget, 1)

        return self._record(str(allocated), f"allocated:{allocated}", signals,
                            PolicyType.TOKEN_BUDGET, agent_type, workspace_id, delta)

    def evaluate_projection_refresh(
        self,
        workspace_id: str,
        projection_age_seconds: float,
        access_count: int,
        semantic_drift_estimate: float = 0.0,
    ) -> PolicyDecision:
        """Evaluate whether a cached projection should be refreshed."""
        self._counter += 1
        policy = self._get_policy("projection_refresh")

        signals = {
            "projection_age_seconds": projection_age_seconds,
            "access_count": access_count,
            "semantic_drift_estimate": semantic_drift_estimate,
        }

        if projection_age_seconds > policy.staleness_threshold_seconds:
            return self._record("refresh", "stale_projection", signals,
                                PolicyType.PROJECTION_REFRESH, None, workspace_id, -0.05)

        if semantic_drift_estimate > 0.3:
            return self._record("refresh", "high_semantic_drift", signals,
                                PolicyType.PROJECTION_REFRESH, None, workspace_id, -0.1)

        return self._record("reuse", "projection_fresh", signals,
                            PolicyType.PROJECTION_REFRESH, None, workspace_id, 0.05)

    # -----------------------------------------------------------------
    # Reporting
    # -----------------------------------------------------------------

    def get_effectiveness_report(self) -> PolicyEffectivenessReport:
        if not self._decisions:
            return PolicyEffectivenessReport()

        by_type: Dict[str, int] = {}
        for d in self._decisions:
            by_type[d.policy_type.value] = by_type.get(d.policy_type.value, 0) + 1

        positive = sum(1 for d in self._decisions if d.optimization_delta > 0)
        avg_delta = sum(d.optimization_delta for d in self._decisions) / len(self._decisions)

        return PolicyEffectivenessReport(
            total_decisions=len(self._decisions),
            decisions_by_type=by_type,
            avg_optimization_delta=avg_delta,
            positive_outcomes=positive,
            effectiveness_ratio=positive / len(self._decisions),
        )

    def get_decision_log(self, limit: int = 200) -> List[Dict[str, Any]]:
        return [d.to_dict() for d in self._decisions[-limit:]]

    # -----------------------------------------------------------------
    # Internals
    # -----------------------------------------------------------------

    def _record(self, outcome, rationale, signals, ptype, agent_type, workspace_id,
                delta=0.0) -> PolicyDecision:
        decision = PolicyDecision(
            decision_id=f"pd-{self._counter:06d}",
            policy_type=ptype,
            agent_type=agent_type,
            workspace_id=workspace_id,
            input_signals=signals,
            outcome=outcome,
            rationale=rationale,
            optimization_delta=delta,
        )
        self._decisions.append(decision)
        return decision

    def _get_policy(self, name: str) -> CoordinationPolicy:
        return self._policies.get(name, CoordinationPolicy(
            name=name, policy_type=PolicyType.DELEGATION,
        ))

    @staticmethod
    def _default_policies() -> List[CoordinationPolicy]:
        return [
            CoordinationPolicy(name="delegation_gate", policy_type=PolicyType.DELEGATION),
            CoordinationPolicy(name="provider_routing", policy_type=PolicyType.PROVIDER_ROUTING),
            CoordinationPolicy(name="token_budget", policy_type=PolicyType.TOKEN_BUDGET),
            CoordinationPolicy(name="projection_refresh", policy_type=PolicyType.PROJECTION_REFRESH),
        ]
