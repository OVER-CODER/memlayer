"""Phase 7.5 — Coordination Intelligence Benchmark Suite.

Measures:
1. Adaptive delegation quality and efficiency
2. Provider routing effectiveness
3. Projection refresh efficiency and token savings
4. Coordination token budget optimization
5. Replay determinism of adaptive decisions
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.agent_runtime import (
    AgentType,
    CoordinationPolicyEngine,
    AdaptiveDelegationEngine,
    ProviderRoutingIntelligence,
    ProjectionRefreshManager,
    CoordinationBudgetOptimizer,
)


# ---------------------------------------------------------------------------
# Benchmark functions
# ---------------------------------------------------------------------------

def benchmark_adaptive_delegation(cycles: int = 20) -> List[Dict[str, Any]]:
    """Measure delegation path optimization quality."""
    rows = []
    engine = AdaptiveDelegationEngine()

    continuity_states = [
        {"drafter": 0.9, "critic": 0.5, "tool_agent": 0.2},
        {"drafter": 0.3, "critic": 0.8, "tool_agent": 0.6},
        {"drafter": 0.5, "critic": 0.5, "tool_agent": 0.5},
    ]

    for cycle in range(cycles):
        for source in AgentType:
            cont_hist = continuity_states[cycle % len(continuity_states)]
            result = engine.select_delegation_target(
                source_type=source,
                workspace_id="ws-bench",
                semantic_continuity_history=cont_hist,
                token_pressure=min(1.0, cycle * 0.05),
                delegation_depth=cycle % 5,
            )
            rows.append({
                "cycle": cycle,
                "source": source.value,
                "selected_target": result.selected_target.value,
                "top_score": result.candidates[0].score if result.candidates else 0,
                "policy_outcome": result.policy_decision.outcome,
                "token_pressure": min(1.0, cycle * 0.05),
                "delegation_depth": cycle % 5,
            })

    metrics = engine.get_delegation_efficiency()
    return rows, metrics


def benchmark_provider_routing(cycles: int = 15) -> List[Dict[str, Any]]:
    """Measure provider selection effectiveness."""
    rows = []
    router = ProviderRoutingIntelligence()
    providers = ["claude", "openai", "gemini"]

    # Simulate quality observations
    quality_seq = {
        "claude": [0.85, 0.88, 0.91, 0.87, 0.93],
        "openai": [0.80, 0.82, 0.79, 0.81, 0.83],
        "gemini": [0.75, 0.78, 0.82, 0.85, 0.88],
    }

    for cycle in range(cycles):
        for agent_type in AgentType:
            # Record quality observations
            for p in providers:
                q = quality_seq[p][cycle % len(quality_seq[p])]
                router.record_quality(agent_type, p, q)

            result = router.select_provider(
                agent_type, "ws-bench", providers,
                token_pressure=cycle * 0.06,
            )
            rows.append({
                "cycle": cycle,
                "agent_type": agent_type.value,
                "selected_provider": result.selected_provider,
                "scores": result.provider_scores,
            })

    return rows, router.get_routing_quality()


def benchmark_projection_refresh(cycles: int = 30) -> List[Dict[str, Any]]:
    """Measure projection refresh efficiency and token savings."""
    rows = []
    mgr = ProjectionRefreshManager()

    projections = [f"proj-{i}" for i in range(8)]
    for p in projections:
        mgr.register_projection(p)

    for cycle in range(cycles):
        key = projections[cycle % len(projections)]
        mgr.record_access(key)

        # Simulate drift on some projections
        if cycle % 7 == 0:
            mgr.update_drift_estimate(key, 0.4)

        dec = mgr.evaluate_refresh(key, workspace_id="ws-bench",
                                    estimated_recompile_tokens=200)
        rows.append({
            "cycle": cycle,
            "cache_key": key,
            "action": dec.action,
            "rationale": dec.rationale,
            "tokens_saved": dec.tokens_saved,
            "projection_age": dec.projection_age_seconds,
        })

    return rows, mgr.get_refresh_metrics()


def benchmark_budget_optimization(cycles: int = 15) -> List[Dict[str, Any]]:
    """Measure token allocation efficiency under varying pressure."""
    rows = []
    opt = CoordinationBudgetOptimizer()

    for cycle in range(cycles):
        pressure = min(1.0, cycle * 0.07)
        quality = {
            "research": 0.9 - cycle * 0.02,
            "drafter": 0.7 + cycle * 0.01,
            "critic": 0.8,
            "tool_agent": 0.6,
        }
        plan = opt.allocate("ws-bench", 4000, list(AgentType),
                            token_pressure=pressure, quality_history=quality)
        rows.append({
            "cycle": cycle,
            "token_pressure": pressure,
            "total_allocated": plan.total_allocated,
            "efficiency_score": plan.efficiency_score,
            "allocations": {k: v.allocated_budget for k, v in plan.allocations.items()},
        })

    return rows, opt.get_budget_metrics()


def benchmark_replay_determinism(repeats: int = 5) -> Dict[str, Any]:
    """Verify all adaptive decisions are replay-deterministic."""
    all_logs = []
    for _ in range(repeats):
        policy = CoordinationPolicyEngine()
        deleg = AdaptiveDelegationEngine(policy)
        router = ProviderRoutingIntelligence(policy)
        refresh = ProjectionRefreshManager(policy)
        budget = CoordinationBudgetOptimizer(policy)

        router.record_quality(AgentType.RESEARCH, "claude", 0.9)
        router.select_provider(AgentType.RESEARCH, "ws-1", ["claude", "openai"])
        deleg.select_delegation_target(AgentType.RESEARCH, "ws-1")
        refresh.register_projection("k1")
        refresh.evaluate_refresh("k1")
        budget.allocate("ws-1", 4000, list(AgentType), token_pressure=0.5)

        log = [(d["outcome"], d["rationale"]) for d in policy.get_decision_log()]
        all_logs.append(log)

    is_deterministic = all(log == all_logs[0] for log in all_logs)
    return {
        "repeats": repeats,
        "is_deterministic": is_deterministic,
        "unique_logs": len(set(str(l) for l in all_logs)),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_benchmark_campaign():
    print("=" * 70)
    print("Phase 7.5 — Coordination Intelligence Benchmark")
    print("=" * 70)

    print("\n[1/5] Adaptive Delegation...")
    deleg_rows, deleg_metrics = benchmark_adaptive_delegation()

    print("[2/5] Provider Routing...")
    routing_rows, routing_metrics = benchmark_provider_routing()

    print("[3/5] Projection Refresh...")
    refresh_rows, refresh_metrics = benchmark_projection_refresh()

    print("[4/5] Budget Optimization...")
    budget_rows, budget_metrics = benchmark_budget_optimization()

    print("[5/5] Replay Determinism...")
    determinism = benchmark_replay_determinism()

    summary = {
        "benchmark_run_at": datetime.now(timezone.utc).isoformat(),
        "delegation": {
            "total_evaluations": deleg_metrics["total_evaluations"],
            "approval_rate": deleg_metrics["approval_rate"],
            "avg_top_score": deleg_metrics["avg_top_candidate_score"],
        },
        "provider_routing": {
            "total_decisions": routing_metrics["total_decisions"],
            "provider_distribution": routing_metrics["provider_selection_distribution"],
        },
        "projection_refresh": {
            "total_evaluations": refresh_metrics["total_evaluations"],
            "reuse_ratio": refresh_metrics["reuse_ratio"],
            "total_tokens_saved": refresh_metrics["total_tokens_saved"],
        },
        "budget_optimization": {
            "total_plans": budget_metrics["total_plans"],
            "avg_efficiency": budget_metrics["avg_efficiency_score"],
            "savings_ratio": budget_metrics["savings_ratio"],
        },
        "determinism": determinism,
    }

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    for category, metrics in summary.items():
        if isinstance(metrics, dict):
            print(f"\n  {category}:")
            for k, v in metrics.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {category}: {metrics}")

    # Persist
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(os.path.dirname(__file__), f"results_{timestamp}")
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(out_dir, "benchmark_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(out_dir, "delegation_quality.json"), "w") as f:
        json.dump(deleg_rows, f, indent=2)
    with open(os.path.join(out_dir, "provider_routing.json"), "w") as f:
        json.dump(routing_rows, f, indent=2)
    with open(os.path.join(out_dir, "projection_refresh.json"), "w") as f:
        json.dump(refresh_rows, f, indent=2)
    with open(os.path.join(out_dir, "budget_optimization.json"), "w") as f:
        json.dump(budget_rows, f, indent=2)
    with open(os.path.join(out_dir, "replay_determinism.json"), "w") as f:
        json.dump(determinism, f, indent=2)

    print(f"\n  Results saved to: {out_dir}")
    return summary


if __name__ == "__main__":
    run_benchmark_campaign()
