"""Tests for Phase 6 View Engine Compiler infrastructure."""

from dataclasses import dataclass
from datetime import datetime
from unittest.mock import MagicMock, Mock
import json

from app.compiler.adaptive_assembly_pipeline import (
    AdaptiveAssemblyResult,
    PipelineStageMetrics,
    PipelineStage,
)
from app.compiler.adaptive_assembly_pipeline import AdaptiveAssemblyPipeline
from app.runtime.integrated_runtime import IntegratedRuntimeSystem
from app.view_engine import (
    ViewType,
    ViewDefinitionFramework,
    WorkspaceSemanticState,
    ViewEngineCompiler,
    ViewReplayEngine,
    ViewDiagnosticsDashboard,
)


@dataclass
class FakeMemory:
    id: str
    raw_content: str
    importance_score: float
    timestamp: datetime
    embedding: list[float]

    def __str__(self) -> str:
        return self.raw_content


def make_runtime() -> IntegratedRuntimeSystem:
    mock_pipeline = MagicMock(spec=AdaptiveAssemblyPipeline)

    def execute_side_effect(query, memories, original_context="", token_budget=4000, provider="claude", workspace_state=None):
        preview = "\n".join(str(memory) for memory in memories[:6])
        compiled = f"QUERY:{query}\nPROVIDER:{provider}\nBUDGET:{token_budget}\n{preview}"
        return AdaptiveAssemblyResult(
            query=query,
            provider=provider,
            compression_mode="balanced",
            compiled_context=compiled,
            reasoning_context="because therefore rationale",
            semantic_memories=preview,
            workspace_summary="summary",
            quality_score=Mock(overall_quality=Mock(return_value=0.9)),
            semantic_retention=0.88,
            token_efficiency=0.81,
            total_duration_ms=10.0,
            stage_metrics=[
                PipelineStageMetrics(
                    stage=PipelineStage.RANKING,
                    duration_ms=2.0,
                    input_count=len(memories),
                    output_count=len(memories),
                ),
                PipelineStageMetrics(
                    stage=PipelineStage.ASSEMBLY,
                    duration_ms=3.5,
                    input_count=len(memories),
                    output_count=1,
                ),
            ],
        )

    mock_pipeline.execute.side_effect = execute_side_effect
    return IntegratedRuntimeSystem(mock_pipeline)


def make_memories(count: int = 24) -> list[FakeMemory]:
    memories = []
    for idx in range(count):
        text = (
            f"Memory {idx} source reference evidence sequence step execute command "
            f"contradiction gap marker {idx}."
        )
        memories.append(
            FakeMemory(
                id=f"m-{idx:04d}",
                raw_content=text,
                importance_score=0.5 + ((idx % 5) * 0.1),
                timestamp=datetime.utcnow(),
                embedding=[(idx + j) / 100.0 for j in range(16)],
            )
        )
    return memories


def make_state() -> WorkspaceSemanticState:
    return WorkspaceSemanticState(
        workspace_id="ws-phase6",
        query="Analyze context continuity and actionability under provider constraints.",
        memories=make_memories(),
        provider="claude",
        token_budget=2800,
        query_type="research",
    )


def test_view_definition_framework_defaults():
    framework = ViewDefinitionFramework()
    defs = framework.list_definitions()
    assert set(defs.keys()) == {"research", "drafter", "tool_agent", "critic"}
    assert framework.get_view_definition(ViewType.RESEARCH).base_token_budget_ratio > 1.0
    assert framework.get_view_definition(ViewType.TOOL_AGENT).compression_preference == "aggressive"


def test_compile_all_views_and_projection_divergence():
    runtime = make_runtime()
    compiler = ViewEngineCompiler(runtime)
    state = make_state()

    compiled = compiler.compile_all_views(state)

    assert set(compiled.keys()) == {"research", "drafter", "tool_agent", "critic"}
    projections = [entry.projection.projection_checksum for entry in compiled.values()]
    assert len(set(projections)) >= 2

    comparison = compiler.compare_compiled_views(list(compiled.values()))
    assert comparison["projection_report"]["projection_count"] == 4
    assert "avg_semantic_divergence" in comparison["projection_report"]


def test_provider_aware_shaping_changes_budget_and_query():
    runtime = make_runtime()
    compiler = ViewEngineCompiler(runtime)
    state = make_state()

    research_claude = compiler.compile_view(state, ViewType.RESEARCH, provider="claude")
    research_openai = compiler.compile_view(state, ViewType.RESEARCH, provider="openai")

    assert research_claude.metrics.token_budget_used != research_openai.metrics.token_budget_used
    assert "[provider=claude]" in research_claude.runtime_trace.assembly_result.query
    assert "[provider=openai]" in research_openai.runtime_trace.assembly_result.query


def test_view_replay_determinism_for_same_state():
    runtime = make_runtime()
    compiler = ViewEngineCompiler(runtime)
    replay_engine = ViewReplayEngine(compiler)
    state = make_state()

    first = replay_engine.replay_view(state, ViewType.CRITIC, provider="gemini")
    second = replay_engine.replay_view(state, ViewType.CRITIC, provider="gemini")

    assert first["deterministic_match"] is True
    assert second["deterministic_match"] is True

    stats = replay_engine.get_replay_statistics()
    assert stats["total_replays"] == 2
    assert stats["determinism_rate"] == 1.0


def test_view_diagnostics_dashboard_snapshot():
    runtime = make_runtime()
    compiler = ViewEngineCompiler(runtime)
    replay_engine = ViewReplayEngine(compiler)
    state = make_state()

    compiled = compiler.compile_all_views(state, provider="openai")
    for view in compiled.values():
        replay_engine.record_view(view)

    dashboard = ViewDiagnosticsDashboard(compiler, replay_engine)
    snapshot = dashboard.capture_snapshot("phase6-snapshot")

    assert snapshot.snapshot_id == "phase6-snapshot"
    assert sum(snapshot.view_counts.values()) >= 4
    assert snapshot.quality_summary["avg_quality"] > 0.0
    assert "total_replays" in snapshot.replay_summary


def test_projection_pairwise_comparison_count_for_four_views():
    runtime = make_runtime()
    compiler = ViewEngineCompiler(runtime)
    state = make_state()

    compiled = compiler.compile_all_views(state, provider="claude")
    report = compiler.compare_compiled_views(list(compiled.values()))

    assert report["projection_report"]["projection_count"] == 4
    assert len(report["projection_report"]["pairwise_comparisons"]) == 6
    assert 0.0 <= report["projection_report"]["avg_semantic_divergence"] <= 1.0


def test_view_export_artifacts(tmp_path):
    runtime = make_runtime()
    compiler = ViewEngineCompiler(runtime)
    replay_engine = ViewReplayEngine(compiler)
    state = make_state()

    compiled = compiler.compile_all_views(state, provider="openai")
    for view in compiled.values():
        replay_engine.record_view(view)

    dashboard = ViewDiagnosticsDashboard(compiler, replay_engine)
    snapshot = dashboard.capture_snapshot("phase6-export")

    history_file = tmp_path / "view_history.json"
    replay_file = tmp_path / "view_replays.json"
    snapshot_file = tmp_path / "view_snapshot.json"

    compiler.export_view_history(str(history_file))
    replay_engine.export_replays(str(replay_file))
    dashboard.export_snapshot(snapshot, str(snapshot_file))

    history_payload = json.loads(history_file.read_text())
    replay_payload = json.loads(replay_file.read_text())
    snapshot_payload = json.loads(snapshot_file.read_text())

    assert history_payload["total_views"] >= 4
    assert replay_payload["statistics"]["total_replays"] >= 4
    assert snapshot_payload["snapshot_id"] == "phase6-export"
