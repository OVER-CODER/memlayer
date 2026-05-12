"""Coordination Budget Optimizer for Phase 7.5.

Optimizes token allocation across coordinated agents, minimizes
redundant semantic expansion, preserves high-value cognition paths,
and balances projection density. All decisions are deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.agent_runtime.agents import AgentType, AGENT_CAPABILITIES
from app.agent_runtime.coordination_policy import (
    CoordinationPolicyEngine,
)


@dataclass
class BudgetAllocation:
    """Token budget allocation for a single agent."""

    agent_type: AgentType
    base_budget: int
    allocated_budget: int
    budget_ratio: float
    pressure_factor: float
    priority_weight: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_type": self.agent_type.value,
            "base_budget": self.base_budget,
            "allocated_budget": self.allocated_budget,
            "budget_ratio": round(self.budget_ratio, 3),
            "pressure_factor": round(self.pressure_factor, 3),
            "priority_weight": round(self.priority_weight, 3),
        }


@dataclass
class CoordinationBudgetPlan:
    """Complete budget plan for a coordinated run."""

    workspace_id: str
    total_budget: int
    total_allocated: int
    token_pressure: float
    allocations: Dict[str, BudgetAllocation] = field(default_factory=dict)
    efficiency_score: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "total_budget": self.total_budget,
            "total_allocated": self.total_allocated,
            "token_pressure": round(self.token_pressure, 3),
            "efficiency_score": round(self.efficiency_score, 4),
            "allocations": {k: v.to_dict() for k, v in self.allocations.items()},
        }


# Priority weights per agent type (sum to 1.0)
_AGENT_PRIORITY: Dict[AgentType, float] = {
    AgentType.RESEARCH: 0.30,
    AgentType.DRAFTER: 0.25,
    AgentType.CRITIC: 0.25,
    AgentType.TOOL_AGENT: 0.20,
}


class CoordinationBudgetOptimizer:
    """Optimizes token allocation across coordinated agents.

    Strategy:
    - Allocate proportionally to agent priority weights
    - Apply capability-aware budget ratios
    - Apply token pressure scaling
    - Track efficiency across coordination cycles

    All allocations are deterministic given the same inputs.
    """

    def __init__(self, policy_engine: Optional[CoordinationPolicyEngine] = None):
        self.policy = policy_engine or CoordinationPolicyEngine()
        self._plans: List[CoordinationBudgetPlan] = []

    def allocate(
        self,
        workspace_id: str,
        total_budget: int,
        agent_types: List[AgentType],
        token_pressure: float = 0.0,
        quality_history: Optional[Dict[str, float]] = None,
    ) -> CoordinationBudgetPlan:
        """Compute optimal token allocation for coordinated agents."""
        q_hist = quality_history or {}

        # Normalize priority weights for requested agents
        raw_weights = {at: _AGENT_PRIORITY.get(at, 0.25) for at in agent_types}
        weight_sum = sum(raw_weights.values())
        weights = {at: w / weight_sum for at, w in raw_weights.items()} if weight_sum > 0 else {at: 1.0 / len(agent_types) for at in agent_types}

        # Pressure factor
        pressure_factor = 1.0
        if token_pressure > 0.7:
            pressure_factor = max(0.6, 1.0 - (token_pressure - 0.7) * 1.0)

        allocations: Dict[str, BudgetAllocation] = {}
        total_allocated = 0

        for agent_type in agent_types:
            caps = AGENT_CAPABILITIES.get(agent_type)
            budget_ratio = caps.max_token_budget_ratio if caps else 1.0

            # Quality-aware adjustment: boost agents with good history
            quality_boost = 1.0
            quality = q_hist.get(agent_type.value, 0.5)
            if quality > 0.8:
                quality_boost = 1.05
            elif quality < 0.4:
                quality_boost = 0.90

            agent_budget = int(
                total_budget * weights[agent_type] * budget_ratio * pressure_factor * quality_boost
            )
            total_allocated += agent_budget

            allocations[agent_type.value] = BudgetAllocation(
                agent_type=agent_type,
                base_budget=int(total_budget * weights[agent_type]),
                allocated_budget=agent_budget,
                budget_ratio=budget_ratio,
                pressure_factor=pressure_factor,
                priority_weight=weights[agent_type],
            )

        # Efficiency: ratio of allocated vs theoretical max
        theoretical_max = total_budget * len(agent_types)
        efficiency = 1.0 - (total_allocated / max(theoretical_max, 1))

        plan = CoordinationBudgetPlan(
            workspace_id=workspace_id,
            total_budget=total_budget,
            total_allocated=total_allocated,
            token_pressure=token_pressure,
            allocations=allocations,
            efficiency_score=max(0.0, efficiency),
        )
        self._plans.append(plan)
        return plan

    def get_budget_metrics(self) -> Dict[str, Any]:
        """Get budget optimization metrics."""
        if not self._plans:
            return {"message": "No budget plans generated"}

        avg_efficiency = sum(p.efficiency_score for p in self._plans) / len(self._plans)
        total_budget = sum(p.total_budget for p in self._plans)
        total_allocated = sum(p.total_allocated for p in self._plans)

        return {
            "total_plans": len(self._plans),
            "avg_efficiency_score": round(avg_efficiency, 4),
            "total_budget_across_plans": total_budget,
            "total_allocated_across_plans": total_allocated,
            "savings_ratio": round(1.0 - total_allocated / max(total_budget * 4, 1), 4),
        }
