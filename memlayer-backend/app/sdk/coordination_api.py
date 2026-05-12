"""Coordination API for Phase 8.

Exposes coordinated agent execution, delegation histories, policy
decisions, and coordination efficiency metrics. Wraps SharedAgentRuntime
and coordination intelligence components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.view_engine.compiler import WorkspaceSemanticState
from app.agent_runtime.agents import AgentType
from app.agent_runtime.runtime_kernel import SharedAgentRuntime, CoordinatedExecutionReport
from app.agent_runtime.coordination_policy import CoordinationPolicyEngine
from app.agent_runtime.adaptive_delegation import AdaptiveDelegationEngine
from app.agent_runtime.budget_optimizer import CoordinationBudgetOptimizer


@dataclass
class CoordinationRequest:
    """Request for a coordinated agent run."""

    workspace_id: str = ""
    provider: str = "claude"
    agent_types: Optional[List[str]] = None
    delegation_chain: Optional[List[Tuple[str, str, str]]] = None
    token_budget: int = 4000
    report_id: Optional[str] = None

    def resolve_agent_types(self) -> List[AgentType]:
        if not self.agent_types:
            return list(AgentType)
        return [AgentType(t) for t in self.agent_types]

    def resolve_delegation_chain(self) -> Optional[List[Tuple[AgentType, AgentType, str]]]:
        if not self.delegation_chain:
            return None
        return [
            (AgentType(src), AgentType(tgt), reason)
            for src, tgt, reason in self.delegation_chain
        ]


@dataclass
class CoordinationSummary:
    """Lightweight coordination result summary."""

    report_id: str
    workspace_id: str
    provider: str
    agent_count: int
    delegation_count: int
    total_tokens_consumed: int
    total_tokens_saved: int
    token_savings_ratio: float
    context_reuse_ratio: float
    coordination_duration_ms: float
    success: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "workspace_id": self.workspace_id,
            "provider": self.provider,
            "agent_count": self.agent_count,
            "delegation_count": self.delegation_count,
            "total_tokens_consumed": self.total_tokens_consumed,
            "total_tokens_saved": self.total_tokens_saved,
            "token_savings_ratio": round(self.token_savings_ratio, 4),
            "context_reuse_ratio": round(self.context_reuse_ratio, 4),
            "coordination_duration_ms": round(self.coordination_duration_ms, 2),
            "success": self.success,
        }


class CoordinationAPI:
    """API for coordinated agent execution and inspection.

    Wraps SharedAgentRuntime and coordination intelligence
    to provide a clean external interface.
    """

    def __init__(
        self,
        runtime: SharedAgentRuntime,
        policy_engine: Optional[CoordinationPolicyEngine] = None,
        delegation_engine: Optional[AdaptiveDelegationEngine] = None,
        budget_optimizer: Optional[CoordinationBudgetOptimizer] = None,
    ):
        self._runtime = runtime
        self._policy = policy_engine or CoordinationPolicyEngine()
        self._delegation = delegation_engine or AdaptiveDelegationEngine(self._policy)
        self._budget = budget_optimizer or CoordinationBudgetOptimizer(self._policy)

    def execute(
        self,
        semantic_state: WorkspaceSemanticState,
        request: Optional[CoordinationRequest] = None,
    ) -> CoordinationSummary:
        """Execute a coordinated agent run."""
        req = request or CoordinationRequest()

        report = self._runtime.execute_coordinated(
            semantic_state=semantic_state,
            agent_types=req.resolve_agent_types(),
            provider=req.provider,
            delegation_chain=req.resolve_delegation_chain(),
            report_id=req.report_id,
        )
        return self._to_summary(report)

    def execute_single_agent(
        self,
        semantic_state: WorkspaceSemanticState,
        agent_type: str = "research",
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a single agent against shared cognition."""
        result = self._runtime.execute_agent(
            agent_type=AgentType(agent_type),
            semantic_state=semantic_state,
            provider=provider,
        )
        return result.to_dict()

    def get_policy_decisions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve recent policy decisions."""
        return self._policy.get_decision_log(limit)

    def get_policy_effectiveness(self) -> Dict[str, Any]:
        """Get policy effectiveness report."""
        return self._policy.get_effectiveness_report().to_dict()

    def get_delegation_efficiency(self) -> Dict[str, Any]:
        """Get adaptive delegation metrics."""
        return self._delegation.get_delegation_efficiency()

    def get_budget_metrics(self) -> Dict[str, Any]:
        """Get budget optimization metrics."""
        return self._budget.get_budget_metrics()

    def get_coordination_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent coordination summaries."""
        reports = self._runtime._reports[-limit:]
        return [self._to_summary(r).to_dict() for r in reports]

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get coordination runtime diagnostics."""
        return self._runtime.get_runtime_diagnostics()

    def _to_summary(self, report: CoordinatedExecutionReport) -> CoordinationSummary:
        return CoordinationSummary(
            report_id=report.report_id,
            workspace_id=report.workspace_id,
            provider=report.provider,
            agent_count=len(report.agent_results),
            delegation_count=report.delegation_count,
            total_tokens_consumed=report.total_tokens_consumed,
            total_tokens_saved=report.total_tokens_saved,
            token_savings_ratio=report.token_savings_ratio,
            context_reuse_ratio=report.context_reuse_ratio,
            coordination_duration_ms=report.coordination_duration_ms,
            success=report.success,
        )
