"""Tests for Phase 6.5 cross-layer runtime evaluation framework."""

from dataclasses import dataclass
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock
import json

from app.compiler.adaptive_assembly_pipeline import (
    AdaptiveAssemblyPipeline,
    AdaptiveAssemblyResult,
    PipelineStage,
    PipelineStageMetrics,
)
from app.runtime import CrossLayerEvaluationFramework
from app.runtime.integrated_runtime import IntegratedRuntimeSystem
from app.view_engine import ViewEngineCompiler, WorkspaceSemanticState


@dataclass
class EvalMemory:
    id: str
    raw_content: str
    importance_score: float
    timestamp: datetime
    embedding: list[float]

    def __str__(self) -> str:
        return self.raw_content


def make_runtime() -> IntegratedRuntimeSystem:
    pipeline = MagicMock(spec=AdaptiveAssemblyPipeline)

    def execute(query, memories, original_context="", token_budget=4000, provider="claude", workspace_state=None):
        context = "\n".join(str(memory) for memory in memories[:8])
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
                    stage=PipelineStage.RANKING,
                    duration_ms=2.0,
                    input_count=len(memories),
                    output_count=len(memories),
                ),
                PipelineStageMetrics(
                    stage=PipelineStage.ASSEMBLY,
                    duration_ms=3.0,
                    input_count=len(memories),
                    output_count=1,
                ),
            ],
        )

    pipeline.execute.side_effect = execute
    return IntegratedRuntimeSystem(pipeline)


def make_state() -> WorkspaceSemanticState:
    memories = []
    for idx in range(28):
        memories.append(
            EvalMemory(
                id=f"mem-{idx:03d}",
                raw_content=(
                    f"Entity{idx} evidence source reference step execute command "
                    f"contradiction gap sequence {idx}."
                ),
                importance_score=0.5 + (idx % 4) * 0.1,
                timestamp=datetime.now(timezone.utc),
                embedding=[(idx + j) / 100.0 for j in range(12)],
            )
        )
    return WorkspaceSemanticState(
        workspace_id="ws-cross-layer",
        query="Evaluate cross-layer semantic continuity and provider robustness.",
        memories=memories,
        provider="claude",
        token_budget=3200,
        query_type="research",
    )


def test_cross_layer_evaluation_full_report():
    runtime = make_runtime()
    compiler = ViewEngineCompiler(runtime)
    framework = CrossLayerEvaluationFramework(compiler)
    state = make_state()

    report = framework.evaluate_runtime_stack(
        semantic_state=state,
        providers=["claude", "openai", "gemini"],
        replay_cycles=2,
        evolution_steps=3,
        report_id="xlayer-1",
    )

    assert report.report_id == "xlayer-1"
    assert report.view_count == 12
    assert report.semantic_fidelity is not None
    assert report.cross_view_consistency is not None
    assert report.replay_integrity is not None
    assert report.replay_integrity.determinism_rate == 1.0
    assert report.token_economics is not None
    assert report.provider_divergence is not None
    assert len(report.provider_divergence.robustness_ranking) == 3


def test_cross_layer_export_report_and_history(tmp_path):
    runtime = make_runtime()
    compiler = ViewEngineCompiler(runtime)
    framework = CrossLayerEvaluationFramework(compiler)
    state = make_state()

    report = framework.evaluate_runtime_stack(
        semantic_state=state,
        providers=["claude", "openai"],
        replay_cycles=1,
        evolution_steps=2,
        report_id="xlayer-export",
    )

    report_file = tmp_path / "cross_layer_report.json"
    history_file = tmp_path / "cross_layer_history.json"
    framework.export_report(report.report_id, str(report_file))
    framework.export_history(str(history_file))

    report_payload = json.loads(report_file.read_text())
    history_payload = json.loads(history_file.read_text())

    assert report_payload["report"]["report_id"] == "xlayer-export"
    assert history_payload["total_reports"] >= 1
    assert history_payload["latest_summary"]["latest_report_id"] == "xlayer-export"


def test_cross_layer_latest_summary_shape():
    runtime = make_runtime()
    compiler = ViewEngineCompiler(runtime)
    framework = CrossLayerEvaluationFramework(compiler)

    assert framework.get_latest_summary()["message"] == "No cross-layer reports available"

    state = make_state()
    framework.evaluate_runtime_stack(semantic_state=state, providers=["claude"])
    summary = framework.get_latest_summary()

    assert summary["workspace_id"] == "ws-cross-layer"
    assert 0.0 <= summary["semantic_preservation"] <= 1.0
    assert 0.0 <= summary["determinism_rate"] <= 1.0
