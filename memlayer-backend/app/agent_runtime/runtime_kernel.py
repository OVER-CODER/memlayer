"""Shared Agent Runtime Kernel for Phase 7.

Coordinates runtime consumers that share compiled semantic cognition.
All agents consume the SAME semantic projections — no agent independently
rebuilds context, retrieves workspace memory, or constructs prompts.

Architecture: Compiler → Virtualization → Coordination.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib
import json
import time
import uuid

from app.runtime.integrated_runtime import IntegratedRuntimeSystem
from app.view_engine.compiler import (
    CompiledSemanticView,
    ViewEngineCompiler,
    WorkspaceSemanticState,
)
from app.view_engine.definitions import ViewType

from app.agent_runtime.agents import (
    AgentType,
    AgentExecutionResult,
    AgentCapabilities,
    AGENT_CAPABILITIES,
    AGENT_VIEW_MAP,
)
from app.agent_runtime.context_bus import SharedContextBus
from app.agent_runtime.agent_registry import AgentStateRegistry
from app.agent_runtime.view_routing import ViewRoutingEngine
from app.agent_runtime.delegation import DelegationRuntime
from app.agent_runtime.coordination_telemetry import (
    CoordinationTelemetryService,
    CoordinationTrace,
    CoordinationDiagnostics,
)


@dataclass
class CoordinatedExecutionPlan:
    """Plan for a coordinated multi-agent execution."""

    plan_id: str
    workspace_id: str
    provider: str
    agent_types: List[AgentType]
    delegation_chain: List[tuple]  # (source_type, target_type, reason)
    state_checksum: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "workspace_id": self.workspace_id,
            "provider": self.provider,
            "agent_types": [a.value for a in self.agent_types],
            "delegation_chain": [
                {"source": s.value, "target": t.value, "reason": r}
                for s, t, r in self.delegation_chain
            ],
            "state_checksum": self.state_checksum,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class CoordinatedExecutionReport:
    """Complete report of a coordinated execution."""

    report_id: str
    workspace_id: str
    provider: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    # Agent results
    agent_results: Dict[str, AgentExecutionResult] = field(default_factory=dict)

    # Cognition metrics
    total_tokens_consumed: int = 0
    total_tokens_saved: int = 0
    token_savings_ratio: float = 0.0
    context_reuse_ratio: float = 0.0
    avg_semantic_continuity: float = 0.0

    # Coordination
    delegation_count: int = 0
    coordination_duration_ms: float = 0.0

    # Status
    success: bool = True
    state_checksum: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "workspace_id": self.workspace_id,
            "provider": self.provider,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_tokens_consumed": self.total_tokens_consumed,
            "total_tokens_saved": self.total_tokens_saved,
            "token_savings_ratio": self.token_savings_ratio,
            "context_reuse_ratio": self.context_reuse_ratio,
            "avg_semantic_continuity": self.avg_semantic_continuity,
            "delegation_count": self.delegation_count,
            "coordination_duration_ms": self.coordination_duration_ms,
            "success": self.success,
            "state_checksum": self.state_checksum,
            "agent_results": {k: v.to_dict() for k, v in self.agent_results.items()},
        }


class SharedAgentRuntime:
    """Coordinated semantic runtime for multiple specialized agents.

    Core responsibilities:
    - Coordinate runtime consumers via shared cognition
    - Manage shared view access through the context bus
    - Orchestrate semantic state usage deterministically
    - Support replayable coordination via telemetry
    - Track token savings from cognition reuse

    Architecture invariant: all agents consume compiled projections,
    never independently rebuild context.
    """

    def __init__(
        self,
        view_compiler: ViewEngineCompiler,
        context_bus: Optional[SharedContextBus] = None,
        agent_registry: Optional[AgentStateRegistry] = None,
        routing_engine: Optional[ViewRoutingEngine] = None,
        delegation_runtime: Optional[DelegationRuntime] = None,
        telemetry: Optional[CoordinationTelemetryService] = None,
    ):
        self.view_compiler = view_compiler
        self.context_bus = context_bus or SharedContextBus(view_compiler)
        self.registry = agent_registry or AgentStateRegistry()
        self.routing = routing_engine or ViewRoutingEngine()
        self.delegation = delegation_runtime or DelegationRuntime()
        self.telemetry = telemetry or CoordinationTelemetryService()

        self._reports: List[CoordinatedExecutionReport] = []

    # -----------------------------------------------------------------
    # Single-agent execution against shared cognition
    # -----------------------------------------------------------------

    def execute_agent(
        self,
        agent_type: AgentType,
        semantic_state: WorkspaceSemanticState,
        provider: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> AgentExecutionResult:
        """Execute a single agent against the shared cognition substrate.

        The agent consumes a compiled view from the context bus.
        It does NOT independently rebuild context.
        """
        start = time.time()
        resolved_provider = provider or semantic_state.provider

        # Register agent if needed
        reg = None
        if agent_id:
            reg = self.registry.get_agent(agent_id)
        if reg is None:
            reg = self.registry.register_agent(agent_type, agent_id=agent_id)

        self.registry.update_agent_status(reg.agent_id, "executing")

        # Get view from shared context bus
        view = self.context_bus.get_view_for_agent(
            agent_id=reg.agent_id,
            agent_type=agent_type,
            semantic_state=semantic_state,
            provider=resolved_provider,
        )

        # Route
        compiled_views = self.context_bus.compile_shared_views(semantic_state, resolved_provider)
        view_type, routed_provider, reused = self.routing.route(
            agent_id=reg.agent_id,
            agent_type=agent_type,
            semantic_state=semantic_state,
            available_views=compiled_views,
            preferred_provider=resolved_provider,
        )

        # Simulate agent execution against compiled view
        execution_id = f"exec-{uuid.uuid4().hex[:12]}"
        output = self._execute_against_view(agent_type, view, semantic_state)

        tokens = len(view.projection.compiled_context.split())
        # Token savings: in isolated mode, each agent would compile its own
        # full context. With shared cognition, they reuse the compiled view.
        independent_cost = self._estimate_independent_cost(semantic_state)
        tokens_saved = max(0, independent_cost - tokens)

        result = AgentExecutionResult(
            agent_id=reg.agent_id,
            agent_type=agent_type,
            execution_id=execution_id,
            view_id=view_type.value,
            provider=routed_provider,
            workspace_id=semantic_state.workspace_id,
            output_content=output,
            output_type=AGENT_CAPABILITIES.get(agent_type, AgentCapabilities(
                primary_objective="", semantic_strengths=[], output_type="generic"
            )).output_type,
            tokens_consumed=tokens,
            tokens_from_shared_view=tokens,
            tokens_saved_vs_independent=tokens_saved,
            semantic_reuse_ratio=1.0 if reused else 0.0,
            projection_checksum=view.projection.projection_checksum,
            quality_score=view.quality_report.overall_quality(),
            semantic_continuity=view.quality_report.reasoning_continuity,
            duration_ms=(time.time() - start) * 1000,
            success=True,
        )

        # Update registry
        self.registry.record_execution(
            agent_id=reg.agent_id,
            execution_id=execution_id,
            tokens_consumed=tokens,
            tokens_saved=tokens_saved,
        )
        self.registry.update_agent_status(reg.agent_id, "idle")

        return result

    # -----------------------------------------------------------------
    # Coordinated multi-agent execution
    # -----------------------------------------------------------------

    def execute_coordinated(
        self,
        semantic_state: WorkspaceSemanticState,
        agent_types: Optional[List[AgentType]] = None,
        provider: Optional[str] = None,
        delegation_chain: Optional[List[tuple]] = None,
        report_id: Optional[str] = None,
    ) -> CoordinatedExecutionReport:
        """Execute coordinated multi-agent run against shared cognition.

        All agents consume the same compiled semantic state.
        Delegation chains enable structured handoffs.
        """
        start = time.time()
        resolved_provider = provider or semantic_state.provider
        resolved_agents = agent_types or list(AgentType)
        resolved_id = report_id or f"coord-{uuid.uuid4().hex[:8]}"

        # Start coordination telemetry
        self.telemetry.start_coordination(
            workspace_id=semantic_state.workspace_id,
            provider=resolved_provider,
        )

        # Pre-compile all shared views (single compilation pass)
        self.context_bus.compile_shared_views(semantic_state, resolved_provider)

        report = CoordinatedExecutionReport(
            report_id=resolved_id,
            workspace_id=semantic_state.workspace_id,
            provider=resolved_provider,
            state_checksum=semantic_state.state_checksum(),
        )

        # Execute each agent
        for agent_type in resolved_agents:
            result = self.execute_agent(
                agent_type=agent_type,
                semantic_state=semantic_state,
                provider=resolved_provider,
            )
            report.agent_results[agent_type.value] = result
            self.telemetry.record_agent_execution(result)

        # Execute delegation chain
        if delegation_chain:
            for source_type, target_type, reason in delegation_chain:
                source_result = report.agent_results.get(source_type.value)
                if not source_result:
                    continue

                deleg_request = self.delegation.create_delegation(
                    source_agent_id=source_result.agent_id,
                    source_agent_type=source_type,
                    target_agent_type=target_type,
                    workspace_id=semantic_state.workspace_id,
                    reason=reason,
                    source_projection_checksum=source_result.projection_checksum,
                )

                target_result = report.agent_results.get(target_type.value)
                if target_result:
                    continuity = self._compute_semantic_continuity(
                        source_result, target_result
                    )
                    deleg_result = self.delegation.complete_delegation(
                        delegation_id=deleg_request.delegation_id,
                        target_agent_id=target_result.agent_id,
                        target_projection_checksum=target_result.projection_checksum,
                        execution_result=target_result,
                        semantic_continuity_score=continuity,
                        tokens_saved=target_result.tokens_saved_vs_independent,
                    )
                    self.telemetry.record_delegation(deleg_result)
                    self.registry.record_delegation(
                        source_agent_id=source_result.agent_id,
                        target_agent_id=target_result.agent_id,
                        delegation_id=deleg_request.delegation_id,
                        workspace_id=semantic_state.workspace_id,
                    )
                    report.delegation_count += 1

        # Compute report metrics
        reuse_metrics = self.context_bus.get_reuse_metrics()
        report.context_reuse_ratio = reuse_metrics.reuse_ratio
        report.total_tokens_consumed = sum(
            r.tokens_consumed for r in report.agent_results.values()
        )
        report.total_tokens_saved = sum(
            r.tokens_saved_vs_independent for r in report.agent_results.values()
        )
        total = report.total_tokens_consumed + report.total_tokens_saved
        report.token_savings_ratio = report.total_tokens_saved / max(total, 1)

        continuities = [
            r.semantic_continuity for r in report.agent_results.values() if r.success
        ]
        report.avg_semantic_continuity = (
            sum(continuities) / len(continuities) if continuities else 0.0
        )

        report.completed_at = datetime.now(timezone.utc)
        report.coordination_duration_ms = (time.time() - start) * 1000

        # Finalize telemetry
        self.telemetry.finalize_coordination(
            context_reuse_ratio=report.context_reuse_ratio,
            success=True,
        )

        self._reports.append(report)
        return report

    # -----------------------------------------------------------------
    # Runtime diagnostics & export
    # -----------------------------------------------------------------

    def get_runtime_diagnostics(self) -> Dict[str, Any]:
        """Get full shared agent runtime diagnostics."""
        return {
            "registry": self.registry.get_registry_summary(),
            "context_bus": self.context_bus.get_shared_state_summary(),
            "routing": self.routing.get_routing_metrics().to_dict(),
            "delegation": self.delegation.get_delegation_statistics(),
            "coordination": self.telemetry.get_diagnostics().to_dict(),
            "total_coordinated_runs": len(self._reports),
        }

    def get_latest_report(self) -> Optional[CoordinatedExecutionReport]:
        return self._reports[-1] if self._reports else None

    def export_runtime_report(self, output_file: str) -> str:
        """Export full runtime report to JSON."""
        payload = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "diagnostics": self.get_runtime_diagnostics(),
            "reports": [r.to_dict() for r in self._reports[-50:]],
        }
        with open(output_file, "w") as f:
            json.dump(payload, f, indent=2)
        return output_file

    # -----------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------

    def _execute_against_view(
        self,
        agent_type: AgentType,
        view: CompiledSemanticView,
        state: WorkspaceSemanticState,
    ) -> str:
        """Simulate agent execution against a compiled view.

        In production, this would invoke the LLM with the compiled projection.
        Here we produce a deterministic structured output based on the view content.
        """
        caps = AGENT_CAPABILITIES.get(agent_type)
        sections = view.projection.semantic_sections
        objective = caps.primary_objective if caps else "general processing"

        parts = [
            f"[{agent_type.value.upper()} AGENT OUTPUT]",
            f"Objective: {objective}",
            f"Provider: {view.projection.provider}",
            f"View: {view.projection.view_type}",
            f"Projection checksum: {view.projection.projection_checksum[:16]}",
            "",
        ]

        for section_name, section_content in sections.items():
            content_preview = section_content[:150] if section_content else "(empty)"
            parts.append(f"## {section_name}")
            parts.append(content_preview)
            parts.append("")

        return "\n".join(parts)

    def _estimate_independent_cost(self, state: WorkspaceSemanticState) -> int:
        """Estimate token cost if an agent compiled context independently."""
        total_content = sum(len(str(m).split()) for m in state.memories)
        return total_content

    def _compute_semantic_continuity(
        self,
        source: AgentExecutionResult,
        target: AgentExecutionResult,
    ) -> float:
        """Compute semantic continuity between source and target execution."""
        if not source.output_content or not target.output_content:
            return 0.0

        source_words = set(source.output_content.lower().split())
        target_words = set(target.output_content.lower().split())
        if not source_words:
            return 0.0

        overlap = source_words & target_words
        return len(overlap) / len(source_words | target_words) if (source_words | target_words) else 0.0
