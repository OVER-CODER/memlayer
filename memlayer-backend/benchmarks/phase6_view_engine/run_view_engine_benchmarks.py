#!/usr/bin/env python3
"""Phase 6 View Engine benchmark suite."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock
import json
import random
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.compiler.adaptive_assembly_pipeline import (
    AdaptiveAssemblyPipeline,
    AdaptiveAssemblyResult,
    PipelineStage,
    PipelineStageMetrics,
)
from app.runtime.integrated_runtime import IntegratedRuntimeSystem
from app.view_engine import (
    ViewEngineCompiler,
    ViewReplayEngine,
    ViewDiagnosticsDashboard,
    ViewType,
    WorkspaceSemanticState,
)


@dataclass
class BenchMemory:
    id: str
    raw_content: str
    importance_score: float
    timestamp: datetime
    embedding: List[float]

    def __str__(self) -> str:
        return self.raw_content


def make_runtime() -> IntegratedRuntimeSystem:
    pipeline = MagicMock(spec=AdaptiveAssemblyPipeline)

    def run(query, memories, original_context="", token_budget=4000, provider="claude", workspace_state=None):
        context = "\n".join(str(memory) for memory in memories[:8])
        compiled = (
            f"QUERY:{query}\nPROVIDER:{provider}\nTOKEN_BUDGET:{token_budget}\n"
            f"WORKSPACE:{(workspace_state or {}).get('workspace_id', 'none')}\n{context}"
        )
        return AdaptiveAssemblyResult(
            query=query,
            provider=provider,
            compression_mode="balanced",
            compiled_context=compiled,
            reasoning_context="because therefore chain",
            semantic_memories=context,
            workspace_summary="workspace summary",
            quality_score=Mock(overall_quality=Mock(return_value=0.9)),
            semantic_retention=0.9,
            token_efficiency=0.82,
            total_duration_ms=12.0,
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

    pipeline.execute.side_effect = run
    return IntegratedRuntimeSystem(pipeline)


def make_memories(count: int, prefix: str) -> List[BenchMemory]:
    memories = []
    for idx in range(count):
        memories.append(
            BenchMemory(
                id=f"{prefix}-m-{idx:05d}",
                raw_content=(
                    f"{prefix} memory {idx}. reference evidence source. "
                    f"sequence step execute command. contradiction gap note {idx}."
                ),
                importance_score=0.5 + ((idx % 5) * 0.1),
                timestamp=datetime.utcnow() - timedelta(minutes=idx % 240),
                embedding=[float((idx + j) % 79) / 79.0 for j in range(24)],
            )
        )
    return memories


def run() -> int:
    random.seed(42)
    out_dir = Path(__file__).resolve().parent / f"results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    out_dir.mkdir(parents=True, exist_ok=True)

    runtime = make_runtime()
    compiler = ViewEngineCompiler(runtime)
    replay = ViewReplayEngine(compiler)
    diagnostics = ViewDiagnosticsDashboard(compiler, replay)

    providers = ["claude", "openai", "gemini"]
    workloads = [
        ("research", 120, "Analyze evidence continuity over long-horizon semantic memory."),
        ("drafting", 90, "Draft coherent narrative from structured semantic context."),
        ("tooling", 70, "Produce deterministic execution context and operational state."),
        ("critique", 110, "Detect contradictions and reasoning gaps in workspace cognition."),
    ]

    benchmark_rows: List[Dict[str, Any]] = []
    for workload_name, memory_count, query in workloads:
        memories = make_memories(memory_count, workload_name)
        for provider in providers:
            state = WorkspaceSemanticState(
                workspace_id=f"ws-{workload_name}-{provider}",
                query=query,
                memories=memories,
                provider=provider,
                token_budget=3200,
                query_type="research",
                workspace_state={"workspace_id": f"ws-{workload_name}-{provider}"},
            )
            compiled = compiler.compile_all_views(state, provider=provider)
            for view in compiled.values():
                replay.record_view(view)
                benchmark_rows.append(
                    {
                        "workload": workload_name,
                        "provider": provider,
                        "view_type": view.view_type.value,
                        "quality": view.quality_report.overall_quality(),
                        "semantic_preservation": view.quality_report.semantic_preservation,
                        "token_efficiency": view.quality_report.token_efficiency,
                        "projection_checksum": view.projection.projection_checksum,
                        "runtime_trace_id": view.runtime_trace.trace_id,
                    }
                )

    # Replay determinism for repeated identical states
    repeat_state = WorkspaceSemanticState(
        workspace_id="ws-repeat",
        query="Validate deterministic view projections under repeated execution.",
        memories=make_memories(80, "repeat"),
        provider="claude",
        token_budget=2800,
        query_type="reasoning",
    )
    determinism_checks = []
    for _ in range(3):
        out = replay.replay_view(repeat_state, ViewType.TOOL_AGENT, provider="claude")
        determinism_checks.append(
            {
                "deterministic_match": out["deterministic_match"],
                "projection_checksum": out["replay_trace"]["projection_checksum"],
            }
        )

    snapshot = diagnostics.capture_snapshot("phase6-benchmark")

    summary = {
        "generated_at": datetime.utcnow().isoformat(),
        "output_dir": str(out_dir),
        "rows": len(benchmark_rows),
        "providers": providers,
        "workloads": [item[0] for item in workloads],
        "avg_quality": sum(row["quality"] for row in benchmark_rows) / max(len(benchmark_rows), 1),
        "avg_token_efficiency": sum(row["token_efficiency"] for row in benchmark_rows) / max(len(benchmark_rows), 1),
        "replay_statistics": replay.get_replay_statistics(),
        "determinism_checks": determinism_checks,
        "diagnostics_snapshot": snapshot.to_dict(),
    }

    with open(out_dir / "view_engine_benchmark_rows.json", "w") as file_obj:
        json.dump(benchmark_rows, file_obj, indent=2)
    with open(out_dir / "view_engine_benchmark_summary.json", "w") as file_obj:
        json.dump(summary, file_obj, indent=2)
    with open(out_dir / "view_engine_diagnostics.txt", "w") as file_obj:
        file_obj.write(diagnostics.render_console_report(snapshot))

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
