"""Phase 7 — Shared Cognition Coordination Benchmark Suite.

Measures:
1. Cognition reuse rate across agents
2. Token savings vs independent agents
3. Semantic coordination consistency
4. Replay determinism for coordinated runs
5. Delegation stability and semantic continuity
6. Cross-agent projection reuse efficiency
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

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
)


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

@dataclass
class BenchMemory:
    id: str
    raw_content: str
    importance_score: float
    timestamp: datetime
    embedding: list

    def __str__(self) -> str:
        return self.raw_content


def _make_runtime():
    pipeline = MagicMock(spec=AdaptiveAssemblyPipeline)

    def execute(query, memories, original_context="", token_budget=4000,
                provider="claude", workspace_state=None):
        context = "\n".join(str(m) for m in memories[:8])
        compiled = (
            f"QUERY:{query}\nPROVIDER:{provider}\nTOKEN_BUDGET:{token_budget}\n"
            f"because therefore hypothesis chain\n{context}"
        )
        return AdaptiveAssemblyResult(
            query=query, provider=provider, compression_mode="balanced",
            compiled_context=compiled,
            reasoning_context="because therefore hypothesis",
            semantic_memories=context, workspace_summary="workspace summary",
            quality_score=Mock(overall_quality=Mock(return_value=0.91)),
            semantic_retention=0.90, token_efficiency=0.84, total_duration_ms=14.0,
            stage_metrics=[
                PipelineStageMetrics(stage=PipelineStage.RANKING, duration_ms=2.0,
                                     input_count=len(memories), output_count=len(memories)),
                PipelineStageMetrics(stage=PipelineStage.ASSEMBLY, duration_ms=3.0,
                                     input_count=len(memories), output_count=1),
            ],
        )

    pipeline.execute.side_effect = execute
    return IntegratedRuntimeSystem(pipeline)


def _make_state(workspace_id: str = "ws-bench", memory_count: int = 30):
    memories = [
        BenchMemory(
            id=f"bm-{i:03d}",
            raw_content=(
                f"Entity{i} evidence source reference step execute "
                f"command contradiction gap sequence {i}."
            ),
            importance_score=0.5 + (i % 4) * 0.1,
            timestamp=datetime.now(timezone.utc),
            embedding=[(i + j) / 100.0 for j in range(12)],
        )
        for i in range(memory_count)
    ]
    return WorkspaceSemanticState(
        workspace_id=workspace_id,
        query="Benchmark shared agent runtime coordination.",
        memories=memories, provider="claude", token_budget=3200,
        query_type="research",
    )


# ---------------------------------------------------------------------------
# Benchmark functions
# ---------------------------------------------------------------------------

def benchmark_cognition_reuse(sar, state, providers, cycles=3):
    """Measure context reuse across multiple coordination cycles."""
    rows = []
    for cycle in range(cycles):
        for provider in providers:
            report = sar.execute_coordinated(
                semantic_state=state, provider=provider,
                report_id=f"reuse-{provider}-{cycle}",
            )
            bus_metrics = sar.context_bus.get_reuse_metrics()
            rows.append({
                "cycle": cycle, "provider": provider,
                "context_reuse_ratio": report.context_reuse_ratio,
                "bus_reuse_ratio": bus_metrics.reuse_ratio,
                "cache_hits": bus_metrics.cache_hits,
                "total_accesses": bus_metrics.total_accesses,
                "tokens_saved": report.total_tokens_saved,
            })
    return rows


def benchmark_token_savings(sar, state, providers):
    """Measure token savings from shared cognition vs independent."""
    rows = []
    for provider in providers:
        report = sar.execute_coordinated(
            semantic_state=state, provider=provider,
        )
        rows.append({
            "provider": provider,
            "total_tokens_consumed": report.total_tokens_consumed,
            "total_tokens_saved": report.total_tokens_saved,
            "token_savings_ratio": report.token_savings_ratio,
            "agents": len(report.agent_results),
        })
    return rows


def benchmark_replay_determinism(state, providers, cycles=5):
    """Verify coordinated runs are deterministic across replays."""
    rows = []
    for provider in providers:
        checksums_per_run = []
        for cycle in range(cycles):
            sar = SharedAgentRuntime(ViewEngineCompiler(_make_runtime()))
            report = sar.execute_coordinated(semantic_state=state, provider=provider)
            run_checksums = {
                at: r.projection_checksum for at, r in report.agent_results.items()
            }
            checksums_per_run.append(run_checksums)

        # All runs must produce identical checksums
        is_deterministic = all(c == checksums_per_run[0] for c in checksums_per_run)
        rows.append({
            "provider": provider,
            "cycles": cycles,
            "is_deterministic": is_deterministic,
            "unique_checksum_sets": len(set(
                json.dumps(c, sort_keys=True) for c in checksums_per_run
            )),
        })
    return rows


def benchmark_delegation_stability(sar, state, provider="claude", cycles=5):
    """Measure delegation chain stability and semantic continuity."""
    chain = [
        (AgentType.RESEARCH, AgentType.DRAFTER, "Synthesize evidence"),
        (AgentType.DRAFTER, AgentType.CRITIC, "Review draft quality"),
        (AgentType.CRITIC, AgentType.TOOL_AGENT, "Execute action plan"),
    ]
    rows = []
    for cycle in range(cycles):
        report = sar.execute_coordinated(
            semantic_state=state, provider=provider,
            delegation_chain=chain,
            report_id=f"deleg-{cycle}",
        )
        deleg_stats = sar.delegation.get_delegation_statistics()
        rows.append({
            "cycle": cycle,
            "delegation_count": report.delegation_count,
            "avg_semantic_continuity": report.avg_semantic_continuity,
            "deleg_total_tokens_saved": deleg_stats.get("total_tokens_saved", 0),
            "success": report.success,
        })
    return rows


def benchmark_projection_reuse(sar, state, providers):
    """Measure cross-agent projection reuse efficiency."""
    for provider in providers:
        sar.execute_coordinated(semantic_state=state, provider=provider)

    routing_metrics = sar.routing.get_routing_metrics()
    return {
        "total_routing_decisions": routing_metrics.total_routing_decisions,
        "projection_reuse_count": routing_metrics.projection_reuse_count,
        "projection_reuse_ratio": routing_metrics.projection_reuse_ratio,
        "provider_distribution": routing_metrics.provider_distribution,
        "view_distribution": routing_metrics.view_distribution,
    }


# ---------------------------------------------------------------------------
# Main campaign runner
# ---------------------------------------------------------------------------

def run_benchmark_campaign():
    providers = ["claude", "openai", "gemini"]
    state = _make_state()

    print("=" * 70)
    print("Phase 7 — Shared Cognition Coordination Benchmark")
    print("=" * 70)

    # Fresh runtime per benchmark category
    sar = SharedAgentRuntime(ViewEngineCompiler(_make_runtime()))

    # 1. Cognition reuse
    print("\n[1/5] Cognition Reuse...")
    reuse_rows = benchmark_cognition_reuse(sar, state, providers, cycles=3)

    # 2. Token savings
    print("[2/5] Token Savings...")
    sar2 = SharedAgentRuntime(ViewEngineCompiler(_make_runtime()))
    savings_rows = benchmark_token_savings(sar2, state, providers)

    # 3. Replay determinism
    print("[3/5] Replay Determinism...")
    determinism_rows = benchmark_replay_determinism(state, providers, cycles=5)

    # 4. Delegation stability
    print("[4/5] Delegation Stability...")
    sar4 = SharedAgentRuntime(ViewEngineCompiler(_make_runtime()))
    delegation_rows = benchmark_delegation_stability(sar4, state, cycles=5)

    # 5. Projection reuse
    print("[5/5] Projection Reuse...")
    sar5 = SharedAgentRuntime(ViewEngineCompiler(_make_runtime()))
    projection_report = benchmark_projection_reuse(sar5, state, providers)

    # Summary
    avg_reuse = sum(r["context_reuse_ratio"] for r in reuse_rows) / len(reuse_rows)
    avg_savings = sum(r["token_savings_ratio"] for r in savings_rows) / len(savings_rows)
    all_deterministic = all(r["is_deterministic"] for r in determinism_rows)
    avg_continuity = sum(r["avg_semantic_continuity"] for r in delegation_rows) / len(delegation_rows)

    summary = {
        "benchmark_run_at": datetime.now(timezone.utc).isoformat(),
        "providers": providers,
        "avg_context_reuse_ratio": avg_reuse,
        "avg_token_savings_ratio": avg_savings,
        "all_deterministic": all_deterministic,
        "avg_delegation_continuity": avg_continuity,
        "projection_reuse_ratio": projection_report["projection_reuse_ratio"],
    }

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    for k, v in summary.items():
        print(f"  {k}: {v}")

    # Persist results
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(os.path.dirname(__file__), f"results_{timestamp}")
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(out_dir, "benchmark_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(out_dir, "cognition_reuse.json"), "w") as f:
        json.dump(reuse_rows, f, indent=2)
    with open(os.path.join(out_dir, "token_savings.json"), "w") as f:
        json.dump(savings_rows, f, indent=2)
    with open(os.path.join(out_dir, "replay_determinism.json"), "w") as f:
        json.dump(determinism_rows, f, indent=2)
    with open(os.path.join(out_dir, "delegation_stability.json"), "w") as f:
        json.dump(delegation_rows, f, indent=2)
    with open(os.path.join(out_dir, "projection_reuse.json"), "w") as f:
        json.dump(projection_report, f, indent=2)

    print(f"\n  Results saved to: {out_dir}")
    return summary


if __name__ == "__main__":
    run_benchmark_campaign()
