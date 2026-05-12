"""Coordination Telemetry for Phase 7 Shared Agent Runtime.

Extends the cognition telemetry stack to support multi-agent coordination:
agent runtime traces, delegation replay, coordination diagnostics,
semantic reuse metrics, and cross-agent token economics.

Every coordination event is replayable, benchmarkable, and
diagnostically explainable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json
import uuid

from app.agent_runtime.agents import AgentType, AgentExecutionResult
from app.agent_runtime.context_bus import ContextReuseMetrics
from app.agent_runtime.delegation import DelegationResult


@dataclass
class CoordinationTrace:
    """Complete trace of a multi-agent coordination cycle."""

    trace_id: str = field(default_factory=lambda: f"coord-{uuid.uuid4().hex[:12]}")
    workspace_id: str = ""
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    provider: str = ""

    # Agent executions
    agent_executions: List[AgentExecutionResult] = field(default_factory=list)

    # Delegations
    delegations: List[DelegationResult] = field(default_factory=list)

    # Aggregated metrics
    total_agents: int = 0
    total_tokens_consumed: int = 0
    total_tokens_saved: int = 0
    context_reuse_ratio: float = 0.0
    avg_semantic_continuity: float = 0.0
    coordination_duration_ms: float = 0.0

    # Status
    success: bool = True
    error_message: Optional[str] = None

    def finalize(self) -> None:
        """Compute final aggregated metrics."""
        self.completed_at = datetime.now(timezone.utc)
        self.coordination_duration_ms = (
            self.completed_at - self.started_at
        ).total_seconds() * 1000

        self.total_agents = len(self.agent_executions)
        self.total_tokens_consumed = sum(
            e.tokens_consumed for e in self.agent_executions
        )
        self.total_tokens_saved = sum(
            e.tokens_saved_vs_independent for e in self.agent_executions
        )

        if self.delegations:
            continuities = [d.semantic_continuity_score for d in self.delegations if d.success]
            self.avg_semantic_continuity = (
                sum(continuities) / len(continuities) if continuities else 0.0
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "workspace_id": self.workspace_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "provider": self.provider,
            "total_agents": self.total_agents,
            "total_tokens_consumed": self.total_tokens_consumed,
            "total_tokens_saved": self.total_tokens_saved,
            "context_reuse_ratio": self.context_reuse_ratio,
            "avg_semantic_continuity": self.avg_semantic_continuity,
            "coordination_duration_ms": self.coordination_duration_ms,
            "success": self.success,
            "error_message": self.error_message,
            "agent_executions": [e.to_dict() for e in self.agent_executions],
            "delegations": [d.to_dict() for d in self.delegations],
        }


@dataclass
class CoordinationDiagnostics:
    """Aggregated diagnostics for coordination quality."""

    total_coordination_cycles: int = 0
    total_agent_executions: int = 0
    total_delegations: int = 0
    total_tokens_consumed: int = 0
    total_tokens_saved: int = 0
    avg_context_reuse_ratio: float = 0.0
    avg_semantic_continuity: float = 0.0
    avg_coordination_duration_ms: float = 0.0
    success_rate: float = 0.0
    token_savings_ratio: float = 0.0
    agents_per_cycle: float = 0.0
    context_reuse_metrics: Optional[ContextReuseMetrics] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_coordination_cycles": self.total_coordination_cycles,
            "total_agent_executions": self.total_agent_executions,
            "total_delegations": self.total_delegations,
            "total_tokens_consumed": self.total_tokens_consumed,
            "total_tokens_saved": self.total_tokens_saved,
            "avg_context_reuse_ratio": self.avg_context_reuse_ratio,
            "avg_semantic_continuity": self.avg_semantic_continuity,
            "avg_coordination_duration_ms": self.avg_coordination_duration_ms,
            "success_rate": self.success_rate,
            "token_savings_ratio": self.token_savings_ratio,
            "agents_per_cycle": self.agents_per_cycle,
            "context_reuse_metrics": (
                self.context_reuse_metrics.to_dict() if self.context_reuse_metrics else None
            ),
        }


class CoordinationTelemetryService:
    """Telemetry service for multi-agent coordination.

    Records coordination traces, computes diagnostics, and supports
    replay-based validation of coordination cycles.
    """

    def __init__(self, max_trace_history: int = 5000):
        self.max_trace_history = max_trace_history
        self._traces: List[CoordinationTrace] = []
        self._current_trace: Optional[CoordinationTrace] = None

    def start_coordination(
        self,
        workspace_id: str,
        provider: str = "",
        trace_id: Optional[str] = None,
    ) -> CoordinationTrace:
        """Begin recording a coordination cycle."""
        trace = CoordinationTrace(
            workspace_id=workspace_id,
            provider=provider,
        )
        if trace_id:
            trace.trace_id = trace_id
        self._current_trace = trace
        return trace

    def record_agent_execution(self, result: AgentExecutionResult) -> None:
        """Record an agent execution within the current coordination cycle."""
        if self._current_trace:
            self._current_trace.agent_executions.append(result)

    def record_delegation(self, result: DelegationResult) -> None:
        """Record a delegation within the current coordination cycle."""
        if self._current_trace:
            self._current_trace.delegations.append(result)

    def finalize_coordination(
        self,
        context_reuse_ratio: float = 0.0,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> CoordinationTrace:
        """Finalize the current coordination cycle."""
        if self._current_trace is None:
            return CoordinationTrace()

        self._current_trace.context_reuse_ratio = context_reuse_ratio
        self._current_trace.success = success
        self._current_trace.error_message = error_message
        self._current_trace.finalize()

        self._traces.append(self._current_trace)
        if len(self._traces) > self.max_trace_history:
            self._traces = self._traces[-self.max_trace_history:]

        result = self._current_trace
        self._current_trace = None
        return result

    def get_diagnostics(self) -> CoordinationDiagnostics:
        """Compute aggregated coordination diagnostics."""
        if not self._traces:
            return CoordinationDiagnostics()

        total = len(self._traces)
        successful = sum(1 for t in self._traces if t.success)
        total_exec = sum(t.total_agents for t in self._traces)
        total_deleg = sum(len(t.delegations) for t in self._traces)
        total_consumed = sum(t.total_tokens_consumed for t in self._traces)
        total_saved = sum(t.total_tokens_saved for t in self._traces)
        reuse_ratios = [t.context_reuse_ratio for t in self._traces]
        continuities = [t.avg_semantic_continuity for t in self._traces if t.delegations]
        durations = [t.coordination_duration_ms for t in self._traces]

        return CoordinationDiagnostics(
            total_coordination_cycles=total,
            total_agent_executions=total_exec,
            total_delegations=total_deleg,
            total_tokens_consumed=total_consumed,
            total_tokens_saved=total_saved,
            avg_context_reuse_ratio=sum(reuse_ratios) / total if total > 0 else 0.0,
            avg_semantic_continuity=sum(continuities) / len(continuities) if continuities else 0.0,
            avg_coordination_duration_ms=sum(durations) / total if total > 0 else 0.0,
            success_rate=successful / total if total > 0 else 0.0,
            token_savings_ratio=total_saved / max(total_consumed, 1),
            agents_per_cycle=total_exec / total if total > 0 else 0.0,
        )

    def get_recent_traces(self, limit: int = 50) -> List[CoordinationTrace]:
        return self._traces[-limit:]

    def replay_trace(self, trace_id: str) -> Optional[CoordinationTrace]:
        """Retrieve a trace by ID for replay analysis."""
        for trace in self._traces:
            if trace.trace_id == trace_id:
                return trace
        return None

    def export_coordination_history(self, output_file: str) -> str:
        """Export coordination telemetry to JSON."""
        payload = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "diagnostics": self.get_diagnostics().to_dict(),
            "total_traces": len(self._traces),
            "traces": [t.to_dict() for t in self._traces[-200:]],
        }
        with open(output_file, "w") as f:
            json.dump(payload, f, indent=2)
        return output_file
