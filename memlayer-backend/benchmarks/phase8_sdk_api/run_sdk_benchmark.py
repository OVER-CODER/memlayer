"""Phase 8 — SDK & Runtime API Benchmark Suite.

Measures:
1. API determinism (repeated calls stability)
2. Replay compatibility (API-triggered executions replay correctly)
3. Workspace scalability (API performance with growing memory size)
4. Projection API efficiency (view reuse)
5. Coordination API efficiency (cognition reuse)
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.sdk import MemLayerSDK


@dataclass
class BenchMemory:
    id: str
    raw_content: str
    importance_score: float
    timestamp: datetime
    embedding: list

    def __str__(self) -> str:
        return self.raw_content


def _memories(count: int = 20):
    return [
        BenchMemory(
            id=f"bm-{i:03d}",
            raw_content=f"Entity{i} evidence source reference step command {i}.",
            importance_score=0.5 + (i % 4) * 0.1,
            timestamp=datetime.now(timezone.utc),
            embedding=[(i + j) / 100.0 for j in range(12)],
        )
        for i in range(count)
    ]


def benchmark_api_determinism(cycles: int = 10):
    """Verify repeated SDK operations produce identical results."""
    rows = []
    for cycle in range(cycles):
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-det")
        sdk.add_memories("ws-det", _memories(15))
        result = sdk.coordinate("ws-det", "determinism benchmark")

        rows.append({
            "cycle": cycle,
            "tokens_consumed": result.total_tokens_consumed,
            "tokens_saved": result.total_tokens_saved,
            "savings_ratio": result.token_savings_ratio,
        })

    all_tokens = [r["tokens_consumed"] for r in rows]
    is_deterministic = len(set(all_tokens)) == 1
    return rows, {"is_deterministic": is_deterministic, "unique_token_counts": len(set(all_tokens))}


def benchmark_replay_compatibility(cycles: int = 5):
    """Verify API-triggered executions replay correctly."""
    results = []
    for cycle in range(cycles):
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-rep")
        sdk.add_memories("ws-rep", _memories(15))

        sdk.coordinate("ws-rep", "replay benchmark")
        replay = sdk.replay_last("ws-rep", "replay benchmark")

        results.append({
            "cycle": cycle,
            "is_deterministic": replay.is_deterministic if replay else False,
            "checksum_match": replay.checksum_match if replay else False,
        })

    all_deterministic = all(r["is_deterministic"] for r in results)
    return results, {"all_deterministic": all_deterministic}


def benchmark_workspace_scalability():
    """Measure API performance with growing memory sizes."""
    results = []
    for mem_count in [10, 25, 50, 100, 200]:
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id=f"ws-scale-{mem_count}")
        sdk.add_memories(f"ws-scale-{mem_count}", _memories(mem_count))

        result = sdk.coordinate(f"ws-scale-{mem_count}", "scalability benchmark")

        results.append({
            "memory_count": mem_count,
            "tokens_consumed": result.total_tokens_consumed,
            "tokens_saved": result.total_tokens_saved,
            "duration_ms": result.coordination_duration_ms,
            "savings_ratio": result.token_savings_ratio,
        })

    return results


def benchmark_projection_reuse():
    """Measure projection reuse efficiency across repeated view calls."""
    sdk = MemLayerSDK()
    sdk.create_workspace(workspace_id="ws-proj")
    sdk.add_memories("ws-proj", _memories(20))

    # Generate views multiple times
    for _ in range(5):
        sdk.generate_views("ws-proj", "projection reuse test")

    diag = sdk.views.get_diagnostics()
    return {
        "reuse_metrics": diag.get("reuse_metrics", {}),
        "cached_views": diag.get("context_bus", {}).get("cached_views", 0),
    }


def benchmark_coordination_efficiency():
    """Measure coordination API efficiency across providers."""
    results = []
    for provider in ["claude", "openai", "gemini"]:
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-eff")
        sdk.add_memories("ws-eff", _memories(20))

        result = sdk.coordinate("ws-eff", "efficiency test", provider=provider)
        results.append({
            "provider": provider,
            "tokens_consumed": result.total_tokens_consumed,
            "tokens_saved": result.total_tokens_saved,
            "savings_ratio": result.token_savings_ratio,
            "reuse_ratio": result.context_reuse_ratio,
        })

    return results


def run_benchmark_campaign():
    print("=" * 70)
    print("Phase 8 — SDK & Runtime API Benchmark")
    print("=" * 70)

    print("\n[1/5] API Determinism...")
    det_rows, det_summary = benchmark_api_determinism()

    print("[2/5] Replay Compatibility...")
    rep_rows, rep_summary = benchmark_replay_compatibility()

    print("[3/5] Workspace Scalability...")
    scale_rows = benchmark_workspace_scalability()

    print("[4/5] Projection Reuse...")
    proj_result = benchmark_projection_reuse()

    print("[5/5] Coordination Efficiency...")
    coord_rows = benchmark_coordination_efficiency()

    summary = {
        "benchmark_run_at": datetime.now(timezone.utc).isoformat(),
        "api_determinism": det_summary,
        "replay_compatibility": rep_summary,
        "scalability": {
            "memory_sizes": [r["memory_count"] for r in scale_rows],
            "durations_ms": [r["duration_ms"] for r in scale_rows],
        },
        "projection_reuse": proj_result,
        "coordination_efficiency": {
            "providers_tested": len(coord_rows),
            "avg_savings_ratio": sum(r["savings_ratio"] for r in coord_rows) / len(coord_rows),
        },
    }

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    for k, v in summary.items():
        if isinstance(v, dict):
            print(f"\n  {k}:")
            for kk, vv in v.items():
                print(f"    {kk}: {vv}")
        else:
            print(f"  {k}: {v}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(os.path.dirname(__file__), f"results_{timestamp}")
    os.makedirs(out_dir, exist_ok=True)

    for name, data in [
        ("summary", summary), ("determinism", det_rows),
        ("replay", rep_rows), ("scalability", scale_rows),
        ("projection_reuse", proj_result), ("coordination", coord_rows),
    ]:
        with open(os.path.join(out_dir, f"{name}.json"), "w") as f:
            json.dump(data, f, indent=2, default=str)

    print(f"\n  Results saved to: {out_dir}")
    return summary


if __name__ == "__main__":
    run_benchmark_campaign()
