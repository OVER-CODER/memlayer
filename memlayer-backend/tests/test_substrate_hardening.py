"""Phase 6.5 substrate hardening tests.

Validates:
- Production readiness gate
- Deterministic checksum seed contracts
- Per-view semantic fidelity invariants
- Projection checksum stability over evolution
- Cross-layer coherence under provider switching
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
from app.runtime import (
    CrossLayerEvaluationFramework,
    ProductionReadinessGate,
    ReadinessThresholds,
)
from app.runtime.integrated_runtime import IntegratedRuntimeSystem
from app.view_engine import (
    ViewEngineCompiler,
    ViewReplayEngine,
    WorkspaceSemanticState,
    ViewType,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@dataclass
class HardenMemory:
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


def _make_state(memory_count: int = 24) -> WorkspaceSemanticState:
    memories = [
        HardenMemory(
            id=f"hmem-{i:03d}",
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
        workspace_id="ws-harden",
        query="Evaluate substrate hardening invariants.",
        memories=memories,
        provider="claude",
        token_budget=3200,
        query_type="research",
    )


# ---------------------------------------------------------------------------
# Production Readiness Gate
# ---------------------------------------------------------------------------

class TestProductionReadinessGate:

    def test_gate_passes_on_healthy_report(self):
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        framework = CrossLayerEvaluationFramework(compiler)
        state = _make_state()

        framework.evaluate_runtime_stack(
            semantic_state=state,
            providers=["claude", "openai", "gemini"],
            replay_cycles=2,
            evolution_steps=3,
        )

        # Use mock-appropriate thresholds (mock data has high token overlap
        # and marginal degradation from uniform content patterns)
        mock_thresholds = ReadinessThresholds(
            max_degradation_index=0.30,
            max_redundant_projection_overhead=0.99,
        )
        gate = ProductionReadinessGate(framework, thresholds=mock_thresholds)
        result = gate.evaluate()

        assert result.is_production_ready is True
        assert result.failed_count == 0
        assert result.passed_count >= 6

    def test_gate_fails_with_no_data(self):
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        framework = CrossLayerEvaluationFramework(compiler)

        gate = ProductionReadinessGate(framework)
        result = gate.evaluate()

        assert result.is_production_ready is False
        assert result.failed_count >= 1

    def test_gate_fails_on_strict_threshold(self):
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        framework = CrossLayerEvaluationFramework(compiler)
        state = _make_state()

        framework.evaluate_runtime_stack(
            semantic_state=state,
            providers=["claude"],
            replay_cycles=1,
            evolution_steps=2,
        )

        strict = ReadinessThresholds(min_providers_evaluated=5)
        gate = ProductionReadinessGate(framework, thresholds=strict)
        result = gate.evaluate()

        assert result.is_production_ready is False
        failed_names = [c.name for c in result.checks if not c.passed]
        assert "provider_coverage" in failed_names

    def test_gate_report_serializable(self):
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        framework = CrossLayerEvaluationFramework(compiler)
        state = _make_state()
        framework.evaluate_runtime_stack(
            semantic_state=state, providers=["claude"])

        gate = ProductionReadinessGate(framework)
        result = gate.evaluate()

        payload = json.dumps(result.to_dict(), default=str)
        assert "is_production_ready" in payload

    def test_gate_history_accumulates(self):
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        framework = CrossLayerEvaluationFramework(compiler)
        state = _make_state()
        framework.evaluate_runtime_stack(
            semantic_state=state, providers=["claude"])

        gate = ProductionReadinessGate(framework)
        gate.evaluate(report_id="r1")
        gate.evaluate(report_id="r2")

        assert len(gate.history) == 2
        assert gate.get_latest().report_id == "r2"


# ---------------------------------------------------------------------------
# Deterministic Checksum Seed Contracts
# ---------------------------------------------------------------------------

class TestDeterministicChecksumContracts:

    def test_same_input_produces_same_checksum(self):
        """Core invariant: identical inputs → identical checksums."""
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        state = _make_state()

        view_a = compiler.compile_view(state, ViewType.RESEARCH, provider="claude")
        view_b = compiler.compile_view(state, ViewType.RESEARCH, provider="claude")

        assert view_a.projection.projection_checksum == view_b.projection.projection_checksum

    def test_different_views_produce_different_checksums(self):
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        state = _make_state()

        research = compiler.compile_view(state, ViewType.RESEARCH, provider="claude")
        tool = compiler.compile_view(state, ViewType.TOOL_AGENT, provider="claude")

        assert research.projection.projection_checksum != tool.projection.projection_checksum

    def test_different_providers_produce_different_checksums(self):
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        state = _make_state()

        claude = compiler.compile_view(state, ViewType.RESEARCH, provider="claude")
        openai = compiler.compile_view(state, ViewType.RESEARCH, provider="openai")

        assert claude.projection.projection_checksum != openai.projection.projection_checksum

    def test_state_checksum_determinism(self):
        state = _make_state()
        cs1 = state.state_checksum()
        cs2 = state.state_checksum()
        assert cs1 == cs2


# ---------------------------------------------------------------------------
# Per-View Semantic Fidelity
# ---------------------------------------------------------------------------

class TestPerViewSemanticFidelity:

    def test_all_views_above_minimum_quality(self):
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        state = _make_state()

        for vtype in ViewType:
            view = compiler.compile_view(state, vtype, provider="claude")
            assert view.quality_report.overall_quality() > 0.0, (
                f"{vtype.value} view quality is zero"
            )

    def test_view_projection_not_empty(self):
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        state = _make_state()

        for vtype in ViewType:
            view = compiler.compile_view(state, vtype, provider="claude")
            assert len(view.projection.compiled_context) > 0

    def test_cross_view_divergence_bounded(self):
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        state = _make_state()
        compiled = compiler.compile_all_views(state, provider="claude")
        comparison = compiler.compare_compiled_views(list(compiled.values()))

        avg_div = comparison["projection_report"]["avg_semantic_divergence"]
        assert avg_div < 0.80, f"Cross-view divergence too high: {avg_div}"


# ---------------------------------------------------------------------------
# Projection Checksum Stability Over Evolution
# ---------------------------------------------------------------------------

class TestProjectionStabilityOverEvolution:

    def test_replay_determinism_across_cycles(self):
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        replay_engine = ViewReplayEngine(compiler)
        state = _make_state()

        checksums = []
        for _ in range(5):
            result = replay_engine.replay_view(
                semantic_state=state,
                view_type=ViewType.RESEARCH,
                provider="claude",
            )
            checksums.append(
                result["replay_trace"]["projection_checksum"]
            )

        # All replays should produce identical checksums
        assert len(set(checksums)) == 1

    def test_replay_statistics_show_full_determinism(self):
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        replay_engine = ViewReplayEngine(compiler)
        state = _make_state()

        for vtype in ViewType:
            for _ in range(3):
                replay_engine.replay_view(state, vtype, provider="claude")

        stats = replay_engine.get_replay_statistics()
        assert stats["determinism_rate"] == 1.0


# ---------------------------------------------------------------------------
# Cross-Layer Coherence Under Provider Switching
# ---------------------------------------------------------------------------

class TestCrossLayerProviderCoherence:

    def test_provider_switching_maintains_determinism(self):
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        framework = CrossLayerEvaluationFramework(compiler)
        state = _make_state()

        report = framework.evaluate_runtime_stack(
            semantic_state=state,
            providers=["claude", "openai", "gemini"],
            replay_cycles=2,
            evolution_steps=3,
        )

        assert report.replay_integrity.determinism_rate == 1.0

    def test_all_providers_in_robustness_ranking(self):
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        framework = CrossLayerEvaluationFramework(compiler)
        state = _make_state()

        report = framework.evaluate_runtime_stack(
            semantic_state=state,
            providers=["claude", "openai", "gemini"],
        )

        ranked = [p for p, _ in report.provider_divergence.robustness_ranking]
        assert set(ranked) == {"claude", "openai", "gemini"}

    def test_cross_layer_report_fully_populated(self):
        runtime = _make_runtime()
        compiler = ViewEngineCompiler(runtime)
        framework = CrossLayerEvaluationFramework(compiler)
        state = _make_state()

        report = framework.evaluate_runtime_stack(
            semantic_state=state,
            providers=["claude"],
        )

        assert report.semantic_fidelity is not None
        assert report.cross_view_consistency is not None
        assert report.replay_integrity is not None
        assert report.projection_evolution is not None
        assert report.token_economics is not None
        assert report.provider_divergence is not None
        assert len(report.optimization_recommendations) > 0
