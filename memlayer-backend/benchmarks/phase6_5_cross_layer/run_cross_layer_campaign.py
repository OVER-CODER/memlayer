#!/usr/bin/env python3
"""Phase 6.5 cross-layer runtime evaluation campaign."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock
import json
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
from app.runtime import CrossLayerEvaluationFramework
from app.runtime.integrated_runtime import IntegratedRuntimeSystem
from app.view_engine import ViewEngineCompiler, WorkspaceSemanticState


@dataclass
class CampaignMemory:
    id: str
    raw_content: str
    importance_score: float
    timestamp: datetime
    embedding: List[float]

    def __str__(self) -> str:
        return self.raw_content


def make_runtime() -> IntegratedRuntimeSystem:
    pipeline = MagicMock(spec=AdaptiveAssemblyPipeline)

    def execute(query, memories, original_context="", token_budget=4000, provider="claude", workspace_state=None):
        context = "\n".join(str(memory) for memory in memories[:10])
        compiled = (
            f"QUERY:{query}\nPROVIDER:{provider}\nTOKEN_BUDGET:{token_budget}\n"
            f"because therefore hypothesis continuity\n{context}"
        )
        return AdaptiveAssemblyResult(
            query=query,
            provider=provider,
            compression_mode="balanced",
            compiled_context=compiled,
            reasoning_context="because therefore hypothesis",
            semantic_memories=context,
            workspace_summary="workspace summary",
            quality_score=Mock(overall_quality=Mock(return_value=0.90)),
            semantic_retention=0.89,
            token_efficiency=0.82,
            total_duration_ms=16.0,
            stage_metrics=[
                PipelineStageMetrics(
                    stage=PipelineStage.RANKING,
                    duration_ms=2.0,
                    input_count=len(memories),
                    output_count=len(memories),
                ),
                PipelineStageMetrics(
                    stage=PipelineStage.ASSEMBLY,
                    duration_ms=4.0,
                    input_count=len(memories),
                    output_count=1,
                ),
            ],
        )

    pipeline.execute.side_effect = execute
    return IntegratedRuntimeSystem(pipeline)


def make_memories(prefix: str, count: int) -> List[CampaignMemory]:
    memories: List[CampaignMemory] = []
    for idx in range(count):
        memories.append(
            CampaignMemory(
                id=f"{prefix}-m-{idx:04d}",
                raw_content=(
                    f"{prefix} entity {idx}. source reference evidence. "
                    f"step execute command sequence. contradiction gap marker {idx}."
                ),
                importance_score=0.5 + (idx % 5) * 0.1,
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=idx % 180),
                embedding=[float((idx + j) % 101) / 101.0 for j in range(20)],
            )
        )
    return memories


def run() -> int:
    runtime = make_runtime()
    compiler = ViewEngineCompiler(runtime)
    evaluator = CrossLayerEvaluationFramework(compiler)

    workloads = [
        ("research", 140, "Evaluate long-horizon semantic fidelity and citation continuity."),
        ("drafting", 100, "Evaluate narrative projection coherence and token economics."),
        ("tooling", 90, "Evaluate deterministic operational projections under token pressure."),
        ("critique", 120, "Evaluate contradiction detection stability across providers."),
    ]

    providers = ["claude", "openai", "gemini"]
    out_dir = Path(__file__).resolve().parent / f"results_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []
    for name, memory_count, query in workloads:
        state = WorkspaceSemanticState(
            workspace_id=f"ws-{name}",
            query=query,
            memories=make_memories(name, memory_count),
            provider="claude",
            token_budget=3600,
            query_type="research",
            workspace_state={"workspace_id": f"ws-{name}"},
        )

        report = evaluator.evaluate_runtime_stack(
            semantic_state=state,
            providers=providers,
            replay_cycles=2,
            evolution_steps=4,
            report_id=f"xlayer-{name}",
        )
        report_dict = report.to_dict()
        rows.append(
            {
                "workload": name,
                "semantic_preservation": report_dict["semantic_fidelity"]["semantic_preservation"],
                "determinism_rate": report_dict["replay_integrity"]["determinism_rate"],
                "avg_view_divergence": report_dict["cross_view_consistency"]["avg_divergence"],
                "semantic_value_per_token": report_dict["token_economics"]["semantic_value_per_token"],
                "top_provider": report_dict["provider_divergence"]["robustness_ranking"][0]["provider"],
            }
        )

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workloads": [item[0] for item in workloads],
        "providers": providers,
        "rows": len(rows),
        "avg_semantic_preservation": sum(row["semantic_preservation"] for row in rows) / len(rows),
        "avg_determinism_rate": sum(row["determinism_rate"] for row in rows) / len(rows),
        "avg_view_divergence": sum(row["avg_view_divergence"] for row in rows) / len(rows),
        "avg_semantic_value_per_token": sum(row["semantic_value_per_token"] for row in rows) / len(rows),
        "latest_summary": evaluator.get_latest_summary(),
    }

    evaluator.export_history(str(out_dir / "cross_layer_history.json"))
    with open(out_dir / "cross_layer_rows.json", "w") as file_obj:
        json.dump(rows, file_obj, indent=2)
    with open(out_dir / "cross_layer_summary.json", "w") as file_obj:
        json.dump(summary, file_obj, indent=2)

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
