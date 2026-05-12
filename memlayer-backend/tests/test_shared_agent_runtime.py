"""Phase 7 — Shared Agent Runtime test suite.

Validates:
- SharedContextBus: compile-once/serve-many, cache hits, reuse metrics
- AgentStateRegistry: registration, lifecycle, coordination events
- ViewRoutingEngine: canonical routing, projection reuse tracking
- DelegationRuntime: delegation chains, semantic continuity
- SharedAgentRuntime: coordinated execution, token savings, determinism
- CoordinationTelemetryService: trace recording, diagnostics
- Cross-agent semantic consistency and replay determinism
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock
import json

import pytest

from app.compiler.adaptive_assembly_pipeline import (
    AdaptiveAssemblyPipeline,
    AdaptiveAssemblyResult,
    PipelineStage,
    PipelineStageMetrics,
)
from app.runtime.integrated_runtime import IntegratedRuntimeSystem
from app.view_engine.compiler import ViewEngineCompiler, WorkspaceSemanticState
from app.view_engine.definitions import ViewType
from app.agent_runtime import (
    AgentType,
    SharedAgentRuntime,
    SharedContextBus,
    AgentStateRegistry,
    DelegationRuntime,
    ViewRoutingEngine,
    CoordinationTelemetryService,
    AgentExecutionResult,
    AGENT_VIEW_MAP,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@dataclass
class AgentMemory:
    id: str
    raw_content: str
    importance_score: float
    timestamp: datetime
    embedding: list[float]

    def __str__(self) -> str:
        return self.raw_content


def _make_runtime() -> IntegratedRuntimeSystem:
    pipeline = MagicMock(spec=AdaptiveAssemblyPipeline)

    def execute(query, memories, original_context="", token_budget=4000,
                provider="claude", workspace_state=None):
        context = "\n".join(str(m) for m in memories[:8])
        compiled = (
            f"QUERY:{query}\nPROVIDER:{provider}\nTOKEN_BUDGET:{token_budget}\n"
            f"because therefore hypothesis chain\n{context}"
        )
        return AdaptiveAssemblyResult(
            query=query,
            provider=provider,
            compression_mode="balanced",
            compiled_context=compiled,
            reasoning_context="because therefore hypothesis",
            semantic_memories=context,
            workspace_summary="workspace summary",
            quality_score=Mock(overall_quality=Mock(return_value=0.91)),
            semantic_retention=0.90,
            token_efficiency=0.84,
            total_duration_ms=14.0,
            stage_metrics=[
                PipelineStageMetrics(
                    stage=PipelineStage.RANKING, duration_ms=2.0,
                    input_count=len(memories), output_count=len(memories),
                ),
                PipelineStageMetrics(
                    stage=PipelineStage.ASSEMBLY, duration_ms=3.0,
                    input_count=len(memories), output_count=1,
                ),
            ],
        )

    pipeline.execute.side_effect = execute
    return IntegratedRuntimeSystem(pipeline)


def _make_state(memory_count: int = 20) -> WorkspaceSemanticState:
    memories = [
        AgentMemory(
            id=f"amem-{i:03d}",
            raw_content=(
                f"Entity{i} evidence source reference step execute command "
                f"contradiction gap sequence {i}."
            ),
            importance_score=0.5 + (i % 4) * 0.1,
            timestamp=datetime.now(timezone.utc),
            embedding=[(i + j) / 100.0 for j in range(12)],
        )
        for i in range(memory_count)
    ]
    return WorkspaceSemanticState(
        workspace_id="ws-agent-test",
        query="Evaluate shared agent runtime coordination.",
        memories=memories,
        provider="claude",
        token_budget=3200,
        query_type="research",
    )


def _make_shared_runtime():
    runtime = _make_runtime()
    compiler = ViewEngineCompiler(runtime)
    return SharedAgentRuntime(compiler)


# ---------------------------------------------------------------------------
# SharedContextBus
# ---------------------------------------------------------------------------

class TestSharedContextBus:

    def test_compile_once_serve_many(self):
        """Views compiled once should be served from cache on subsequent access."""
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        bus = SharedContextBus(compiler)
        state = _make_state()

        # First compilation
        views1 = bus.compile_shared_views(state, provider="claude")
        assert len(views1) == 4  # RESEARCH, DRAFTER, TOOL_AGENT, CRITIC

        # Second access should be cached
        views2 = bus.compile_shared_views(state, provider="claude")
        assert len(views2) == 4

        # Checksums must match (same compiled projections)
        for vt in ViewType:
            assert views1[vt.value].projection.projection_checksum == \
                   views2[vt.value].projection.projection_checksum

    def test_agent_view_access_tracking(self):
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        bus = SharedContextBus(compiler)
        state = _make_state()

        bus.get_view_for_agent("agent-1", AgentType.RESEARCH, state)
        bus.get_view_for_agent("agent-2", AgentType.DRAFTER, state)
        bus.get_view_for_agent("agent-3", AgentType.RESEARCH, state)

        metrics = bus.get_reuse_metrics()
        assert metrics.total_accesses == 3
        # agent-3 RESEARCH access should be a cache hit (compiled for agent-1)
        assert metrics.cache_hits >= 1

    def test_reuse_ratio_increases_with_shared_access(self):
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        bus = SharedContextBus(compiler)
        state = _make_state()

        # First pass: all cold
        for at in AgentType:
            bus.get_view_for_agent(f"a-{at.value}", at, state)

        # Second pass: all cached
        for at in AgentType:
            bus.get_view_for_agent(f"b-{at.value}", at, state)

        metrics = bus.get_reuse_metrics()
        assert metrics.reuse_ratio > 0.0
        assert metrics.tokens_saved_by_reuse > 0

    def test_invalidation_clears_cache(self):
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        bus = SharedContextBus(compiler)
        state = _make_state()

        bus.compile_shared_views(state)
        assert bus.get_shared_state_summary()["cached_views"] > 0

        cleared = bus.invalidate()
        assert cleared > 0
        assert bus.get_shared_state_summary()["cached_views"] == 0

    def test_workspace_scoped_invalidation(self):
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        bus = SharedContextBus(compiler)

        state1 = _make_state()
        state1.workspace_id = "ws-A"
        state2 = _make_state()
        state2.workspace_id = "ws-B"

        bus.compile_shared_views(state1)
        bus.compile_shared_views(state2)
        assert bus.get_shared_state_summary()["cached_views"] == 8  # 4 views * 2 workspaces

        bus.invalidate(workspace_id="ws-A")
        assert bus.get_shared_state_summary()["cached_views"] == 4


# ---------------------------------------------------------------------------
# AgentStateRegistry
# ---------------------------------------------------------------------------

class TestAgentStateRegistry:

    def test_register_and_retrieve(self):
        registry = AgentStateRegistry()
        reg = registry.register_agent(AgentType.RESEARCH, agent_id="r-1")

        assert reg.agent_id == "r-1"
        assert reg.agent_type == AgentType.RESEARCH
        assert reg.status == "idle"
        assert "research" in reg.subscribed_views

        found = registry.get_agent("r-1")
        assert found is not None
        assert found.agent_id == "r-1"

    def test_execution_tracking(self):
        registry = AgentStateRegistry()
        reg = registry.register_agent(AgentType.DRAFTER, agent_id="d-1")

        registry.record_execution("d-1", "exec-001", tokens_consumed=500, tokens_saved=200)
        registry.record_execution("d-1", "exec-002", tokens_consumed=600, tokens_saved=250)

        assert reg.total_executions == 2
        assert reg.total_tokens_consumed == 1100
        assert reg.total_tokens_saved == 450

    def test_delegation_events_recorded(self):
        registry = AgentStateRegistry()
        registry.register_agent(AgentType.RESEARCH, agent_id="r-1")
        registry.register_agent(AgentType.DRAFTER, agent_id="d-1")

        registry.record_delegation("r-1", "d-1", "deleg-001", workspace_id="ws-1")

        events = registry.get_coordination_timeline()
        deleg_events = [e for e in events if e.event_type == "delegation"]
        assert len(deleg_events) == 1
        assert deleg_events[0].source_agent_id == "r-1"
        assert deleg_events[0].target_agent_id == "d-1"

    def test_registry_summary(self):
        registry = AgentStateRegistry()
        for at in AgentType:
            registry.register_agent(at)

        summary = registry.get_registry_summary()
        assert summary["total_agents"] == 4
        assert len(summary["by_type"]) == 4

    def test_get_agents_by_type(self):
        registry = AgentStateRegistry()
        registry.register_agent(AgentType.CRITIC, agent_id="c-1")
        registry.register_agent(AgentType.CRITIC, agent_id="c-2")
        registry.register_agent(AgentType.RESEARCH, agent_id="r-1")

        critics = registry.get_agents_by_type(AgentType.CRITIC)
        assert len(critics) == 2


# ---------------------------------------------------------------------------
# ViewRoutingEngine
# ---------------------------------------------------------------------------

class TestViewRoutingEngine:

    def test_canonical_routing(self):
        engine = ViewRoutingEngine()

        assert engine.resolve_view_type(AgentType.RESEARCH) == ViewType.RESEARCH
        assert engine.resolve_view_type(AgentType.DRAFTER) == ViewType.DRAFTER
        assert engine.resolve_view_type(AgentType.TOOL_AGENT) == ViewType.TOOL_AGENT
        assert engine.resolve_view_type(AgentType.CRITIC) == ViewType.CRITIC

    def test_routing_metrics(self):
        engine = ViewRoutingEngine()
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        state = _make_state()
        views = compiler.compile_all_views(state, provider="claude")

        for at in AgentType:
            engine.route(f"a-{at.value}", at, state, views)

        metrics = engine.get_routing_metrics()
        assert metrics.total_routing_decisions == 4
        assert len(metrics.view_distribution) == 4

    def test_provider_resolution(self):
        engine = ViewRoutingEngine()
        state = _make_state()

        # Explicit preference overrides
        provider = engine.resolve_provider(AgentType.RESEARCH, state, preferred_provider="gemini")
        assert provider == "gemini"

        # Falls back to capability profile default
        provider = engine.resolve_provider(AgentType.RESEARCH, state)
        assert provider in ["claude", "openai", "gemini"]


# ---------------------------------------------------------------------------
# DelegationRuntime
# ---------------------------------------------------------------------------

class TestDelegationRuntime:

    def test_create_and_complete_delegation(self):
        deleg = DelegationRuntime()

        request = deleg.create_delegation(
            source_agent_id="r-1",
            source_agent_type=AgentType.RESEARCH,
            target_agent_type=AgentType.DRAFTER,
            workspace_id="ws-1",
            reason="Synthesize research findings",
            source_projection_checksum="abc123",
        )

        result = deleg.complete_delegation(
            delegation_id=request.delegation_id,
            target_agent_id="d-1",
            target_projection_checksum="def456",
            semantic_continuity_score=0.85,
            tokens_saved=300,
        )

        assert result.success is True
        assert result.semantic_continuity_score == 0.85
        assert result.tokens_saved_by_delegation == 300

    def test_delegation_chain_tracking(self):
        deleg = DelegationRuntime()

        # Create 3 delegations in the same chain
        for i, (src, tgt) in enumerate([
            (AgentType.RESEARCH, AgentType.DRAFTER),
            (AgentType.DRAFTER, AgentType.CRITIC),
            (AgentType.CRITIC, AgentType.TOOL_AGENT),
        ]):
            req = deleg.create_delegation(
                source_agent_id=f"a-{src.value}",
                source_agent_type=src,
                target_agent_type=tgt,
                workspace_id="ws-chain",
                reason=f"Step {i}",
                chain_id="chain-1",
            )
            deleg.complete_delegation(
                delegation_id=req.delegation_id,
                target_agent_id=f"a-{tgt.value}",
                semantic_continuity_score=0.80 + i * 0.05,
                tokens_saved=100 * (i + 1),
                chain_id="chain-1",
            )

        chain = deleg.get_chain("chain-1")
        assert chain is not None
        assert len(chain.delegations) == 3
        assert chain.total_tokens_saved == 600
        assert chain.avg_semantic_continuity > 0.0

    def test_delegation_statistics(self):
        deleg = DelegationRuntime()
        req = deleg.create_delegation(
            source_agent_id="r-1",
            source_agent_type=AgentType.RESEARCH,
            target_agent_type=AgentType.DRAFTER,
            workspace_id="ws-1",
            reason="test",
        )
        deleg.complete_delegation(
            delegation_id=req.delegation_id,
            target_agent_id="d-1",
            semantic_continuity_score=0.9,
            tokens_saved=200,
        )

        stats = deleg.get_delegation_statistics()
        assert stats["total_delegations"] == 1
        assert stats["success_rate"] == 1.0
        assert stats["total_tokens_saved"] == 200


# ---------------------------------------------------------------------------
# CoordinationTelemetryService
# ---------------------------------------------------------------------------

class TestCoordinationTelemetry:

    def test_coordination_trace_lifecycle(self):
        telemetry = CoordinationTelemetryService()

        telemetry.start_coordination(workspace_id="ws-1", provider="claude")
        telemetry.record_agent_execution(AgentExecutionResult(
            agent_id="r-1", agent_type=AgentType.RESEARCH,
            execution_id="e-1", view_id="research", provider="claude",
            workspace_id="ws-1", tokens_consumed=500,
        ))

        trace = telemetry.finalize_coordination(context_reuse_ratio=0.75)

        assert trace.success is True
        assert trace.total_agents == 1
        assert trace.context_reuse_ratio == 0.75
        assert trace.coordination_duration_ms > 0

    def test_diagnostics_aggregation(self):
        telemetry = CoordinationTelemetryService()

        for i in range(3):
            telemetry.start_coordination(workspace_id="ws-1")
            telemetry.record_agent_execution(AgentExecutionResult(
                agent_id=f"a-{i}", agent_type=AgentType.RESEARCH,
                execution_id=f"e-{i}", view_id="research", provider="claude",
                workspace_id="ws-1", tokens_consumed=100,
                tokens_saved_vs_independent=50,
            ))
            telemetry.finalize_coordination(context_reuse_ratio=0.5 + i * 0.1)

        diag = telemetry.get_diagnostics()
        assert diag.total_coordination_cycles == 3
        assert diag.total_agent_executions == 3
        assert diag.success_rate == 1.0

    def test_trace_replay(self):
        telemetry = CoordinationTelemetryService()
        telemetry.start_coordination(workspace_id="ws-1")
        trace = telemetry.finalize_coordination()

        replayed = telemetry.replay_trace(trace.trace_id)
        assert replayed is not None
        assert replayed.trace_id == trace.trace_id


# ---------------------------------------------------------------------------
# SharedAgentRuntime (integration)
# ---------------------------------------------------------------------------

class TestSharedAgentRuntime:

    def test_single_agent_execution(self):
        sar = _make_shared_runtime()
        state = _make_state()

        result = sar.execute_agent(AgentType.RESEARCH, state, provider="claude")

        assert result.success is True
        assert result.agent_type == AgentType.RESEARCH
        assert result.tokens_consumed > 0
        assert result.tokens_from_shared_view > 0
        assert len(result.output_content) > 0
        assert result.projection_checksum != ""

    def test_all_agent_types_execute(self):
        sar = _make_shared_runtime()
        state = _make_state()

        for at in AgentType:
            result = sar.execute_agent(at, state, provider="claude")
            assert result.success is True
            assert result.agent_type == at

    def test_coordinated_execution_all_agents(self):
        sar = _make_shared_runtime()
        state = _make_state()

        report = sar.execute_coordinated(semantic_state=state, provider="claude")

        assert report.success is True
        assert len(report.agent_results) == 4
        assert report.total_tokens_consumed > 0
        assert report.coordination_duration_ms > 0

        # All agent types should be present
        for at in AgentType:
            assert at.value in report.agent_results

    def test_coordinated_with_delegation_chain(self):
        sar = _make_shared_runtime()
        state = _make_state()

        chain = [
            (AgentType.RESEARCH, AgentType.DRAFTER, "Synthesize findings"),
            (AgentType.DRAFTER, AgentType.CRITIC, "Review draft"),
        ]

        report = sar.execute_coordinated(
            semantic_state=state,
            provider="claude",
            delegation_chain=chain,
        )

        assert report.delegation_count == 2
        assert report.success is True

    def test_token_savings_from_shared_cognition(self):
        """Core thesis: shared cognition saves tokens vs independent agents."""
        sar = _make_shared_runtime()
        state = _make_state()

        report = sar.execute_coordinated(semantic_state=state, provider="claude")

        # Total tokens saved should be positive (shared > independent)
        assert report.total_tokens_saved > 0
        assert report.token_savings_ratio > 0.0

    def test_context_reuse_across_agents(self):
        """All agents should consume the same compiled views."""
        sar = _make_shared_runtime()
        state = _make_state()

        sar.execute_coordinated(semantic_state=state, provider="claude")

        bus_metrics = sar.context_bus.get_reuse_metrics()
        # Should have cache hits from shared compilation
        assert bus_metrics.total_accesses >= 4
        assert bus_metrics.cache_hits > 0

    def test_deterministic_coordinated_execution(self):
        """Repeated coordinated runs should produce identical checksums."""
        state = _make_state()
        checksums_run1 = {}
        checksums_run2 = {}

        sar1 = _make_shared_runtime()
        report1 = sar1.execute_coordinated(semantic_state=state, provider="claude")
        for at, result in report1.agent_results.items():
            checksums_run1[at] = result.projection_checksum

        sar2 = _make_shared_runtime()
        report2 = sar2.execute_coordinated(semantic_state=state, provider="claude")
        for at, result in report2.agent_results.items():
            checksums_run2[at] = result.projection_checksum

        assert checksums_run1 == checksums_run2

    def test_runtime_diagnostics(self):
        sar = _make_shared_runtime()
        state = _make_state()
        sar.execute_coordinated(semantic_state=state, provider="claude")

        diag = sar.get_runtime_diagnostics()
        assert "registry" in diag
        assert "context_bus" in diag
        assert "routing" in diag
        assert "delegation" in diag
        assert "coordination" in diag
        assert diag["total_coordinated_runs"] == 1

    def test_multi_provider_coordination(self):
        sar = _make_shared_runtime()
        state = _make_state()

        for provider in ["claude", "openai", "gemini"]:
            report = sar.execute_coordinated(
                semantic_state=state,
                provider=provider,
            )
            assert report.success is True
            assert report.provider == provider

        assert len(sar._reports) == 3

    def test_report_serializable(self):
        sar = _make_shared_runtime()
        state = _make_state()
        report = sar.execute_coordinated(semantic_state=state, provider="claude")

        payload = json.dumps(report.to_dict(), default=str)
        assert "agent_results" in payload
        assert "token_savings_ratio" in payload

    def test_export_runtime_report(self, tmp_path):
        sar = _make_shared_runtime()
        state = _make_state()
        sar.execute_coordinated(semantic_state=state, provider="claude")

        out_file = str(tmp_path / "runtime_report.json")
        sar.export_runtime_report(out_file)

        data = json.loads(open(out_file).read())
        assert "diagnostics" in data
        assert "reports" in data


# ---------------------------------------------------------------------------
# Cross-agent semantic consistency
# ---------------------------------------------------------------------------

class TestCrossAgentSemanticConsistency:

    def test_shared_state_checksum_consistency(self):
        """All agents in a coordinated run share the same state checksum."""
        sar = _make_shared_runtime()
        state = _make_state()
        report = sar.execute_coordinated(semantic_state=state, provider="claude")

        assert report.state_checksum == state.state_checksum()

    def test_agents_consume_same_workspace(self):
        """All agent results reference the same workspace."""
        sar = _make_shared_runtime()
        state = _make_state()
        report = sar.execute_coordinated(semantic_state=state, provider="claude")

        for result in report.agent_results.values():
            assert result.workspace_id == state.workspace_id

    def test_long_horizon_coordination(self):
        """Multiple coordination cycles should accumulate telemetry correctly."""
        sar = _make_shared_runtime()
        state = _make_state()

        for i in range(5):
            sar.execute_coordinated(
                semantic_state=state,
                provider="claude",
                report_id=f"cycle-{i}",
            )

        assert len(sar._reports) == 5
        diag = sar.get_runtime_diagnostics()
        assert diag["coordination"]["total_coordination_cycles"] == 5
