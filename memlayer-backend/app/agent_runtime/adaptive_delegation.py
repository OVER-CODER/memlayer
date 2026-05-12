"""Adaptive Delegation Engine for Phase 7.5.

Dynamically chooses delegation targets based on semantic continuity,
token pressure, and projection specialization. All decisions are
deterministic given the same input signals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.agent_runtime.agents import AgentType, AGENT_CAPABILITIES
from app.agent_runtime.coordination_policy import (
    CoordinationPolicyEngine,
    PolicyDecision,
)


@dataclass
class DelegationCandidate:
    """A scored delegation target."""

    target_type: AgentType
    score: float
    rationale: str
    estimated_token_saving: int = 0
    estimated_continuity: float = 0.0


@dataclass
class AdaptiveDelegationResult:
    """Outcome of an adaptive delegation decision."""

    source_type: AgentType
    selected_target: AgentType
    candidates: List[DelegationCandidate]
    policy_decision: PolicyDecision
    workspace_id: str = ""
    token_pressure: float = 0.0
    delegation_depth: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type.value,
            "selected_target": self.selected_target.value,
            "candidates": [
                {"target": c.target_type.value, "score": c.score, "rationale": c.rationale}
                for c in self.candidates
            ],
            "policy_outcome": self.policy_decision.outcome,
            "workspace_id": self.workspace_id,
            "token_pressure": self.token_pressure,
            "delegation_depth": self.delegation_depth,
        }


# Canonical delegation affinities (source → preferred targets, scored)
_DELEGATION_AFFINITIES: Dict[AgentType, List[Tuple[AgentType, float]]] = {
    AgentType.RESEARCH: [(AgentType.DRAFTER, 0.9), (AgentType.CRITIC, 0.7), (AgentType.TOOL_AGENT, 0.4)],
    AgentType.DRAFTER: [(AgentType.CRITIC, 0.9), (AgentType.TOOL_AGENT, 0.6), (AgentType.RESEARCH, 0.3)],
    AgentType.CRITIC: [(AgentType.DRAFTER, 0.8), (AgentType.RESEARCH, 0.7), (AgentType.TOOL_AGENT, 0.5)],
    AgentType.TOOL_AGENT: [(AgentType.CRITIC, 0.7), (AgentType.RESEARCH, 0.6), (AgentType.DRAFTER, 0.4)],
}


class AdaptiveDelegationEngine:
    """Selects optimal delegation targets using policy-driven scoring.

    Scoring factors:
    - Canonical affinity (structural delegation preference)
    - Token pressure (under pressure, prefer token-efficient agents)
    - Semantic continuity history (prefer high-continuity paths)
    - Delegation depth (penalize deep chains)

    All decisions are deterministic given the same input signals.
    """

    def __init__(self, policy_engine: Optional[CoordinationPolicyEngine] = None):
        self.policy = policy_engine or CoordinationPolicyEngine()
        self._results: List[AdaptiveDelegationResult] = []

    def select_delegation_target(
        self,
        source_type: AgentType,
        workspace_id: str,
        available_targets: Optional[List[AgentType]] = None,
        semantic_continuity_history: Optional[Dict[str, float]] = None,
        token_pressure: float = 0.0,
        delegation_depth: int = 0,
    ) -> AdaptiveDelegationResult:
        """Select the optimal delegation target for a source agent."""
        targets = available_targets or [t for t, _ in _DELEGATION_AFFINITIES.get(source_type, [])]
        continuity_hist = semantic_continuity_history or {}

        candidates: List[DelegationCandidate] = []
        for target in targets:
            affinity = self._get_affinity(source_type, target)
            continuity = continuity_hist.get(target.value, 0.5)
            depth_penalty = max(0.0, 1.0 - delegation_depth * 0.15)
            pressure_bonus = 0.0

            # Under token pressure, prefer agents with lower budget ratios
            if token_pressure > 0.7:
                caps = AGENT_CAPABILITIES.get(target)
                if caps and caps.max_token_budget_ratio < 1.0:
                    pressure_bonus = 0.15

            score = (affinity * 0.4 + continuity * 0.3 + depth_penalty * 0.2 + pressure_bonus * 0.1)

            candidates.append(DelegationCandidate(
                target_type=target,
                score=round(score, 4),
                rationale=f"affinity={affinity:.2f} continuity={continuity:.2f} depth_pen={depth_penalty:.2f}",
                estimated_continuity=continuity,
            ))

        # Sort deterministically: by score desc, then by agent name for tiebreak
        candidates.sort(key=lambda c: (-c.score, c.target_type.value))
        selected = candidates[0] if candidates else DelegationCandidate(
            target_type=source_type, score=0.0, rationale="no_candidates",
        )

        # Evaluate policy gate
        policy_decision = self.policy.evaluate_delegation(
            source_type=source_type,
            target_type=selected.target_type,
            workspace_id=workspace_id,
            semantic_continuity=selected.estimated_continuity,
            delegation_depth=delegation_depth,
            token_pressure=token_pressure,
        )

        result = AdaptiveDelegationResult(
            source_type=source_type,
            selected_target=selected.target_type,
            candidates=candidates,
            policy_decision=policy_decision,
            workspace_id=workspace_id,
            token_pressure=token_pressure,
            delegation_depth=delegation_depth,
        )
        self._results.append(result)
        return result

    def get_delegation_efficiency(self) -> Dict[str, Any]:
        """Get delegation efficiency metrics."""
        if not self._results:
            return {"message": "No delegations evaluated"}

        allowed = sum(1 for r in self._results if r.policy_decision.outcome == "allow")
        denied = sum(1 for r in self._results if r.policy_decision.outcome == "deny")
        avg_score = sum(r.candidates[0].score for r in self._results if r.candidates) / len(self._results)

        return {
            "total_evaluations": len(self._results),
            "allowed": allowed,
            "denied": denied,
            "deferred": len(self._results) - allowed - denied,
            "avg_top_candidate_score": round(avg_score, 4),
            "approval_rate": allowed / len(self._results),
        }

    def _get_affinity(self, source: AgentType, target: AgentType) -> float:
        affinities = _DELEGATION_AFFINITIES.get(source, [])
        for t, score in affinities:
            if t == target:
                return score
        return 0.2  # default low affinity
