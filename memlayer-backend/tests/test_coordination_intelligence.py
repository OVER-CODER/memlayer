"""Phase 7.5 — Coordination Intelligence test suite.

Validates:
- CoordinationPolicyEngine: deterministic policies, effectiveness tracking
- AdaptiveDelegationEngine: target selection, policy gating, efficiency
- ProviderRoutingIntelligence: quality-based routing, provider selection
- ProjectionRefreshManager: staleness detection, reuse decisions
- CoordinationBudgetOptimizer: allocation, pressure scaling, efficiency
- Cross-component integration and replay determinism
"""

import pytest

from app.agent_runtime import (
    AgentType,
    CoordinationPolicyEngine,
    CoordinationPolicy,
    PolicyType,
    AdaptiveDelegationEngine,
    ProviderRoutingIntelligence,
    ProjectionRefreshManager,
    CoordinationBudgetOptimizer,
)


# ---------------------------------------------------------------------------
# CoordinationPolicyEngine
# ---------------------------------------------------------------------------

class TestCoordinationPolicyEngine:

    def test_delegation_allow(self):
        engine = CoordinationPolicyEngine()
        dec = engine.evaluate_delegation(
            AgentType.RESEARCH, AgentType.DRAFTER,
            workspace_id="ws-1", semantic_continuity=0.7, delegation_depth=0,
        )
        assert dec.outcome == "allow"
        assert dec.optimization_delta > 0

    def test_delegation_deny_max_depth(self):
        engine = CoordinationPolicyEngine()
        dec = engine.evaluate_delegation(
            AgentType.RESEARCH, AgentType.DRAFTER,
            workspace_id="ws-1", delegation_depth=5,
        )
        assert dec.outcome == "deny"
        assert "max_depth" in dec.rationale

    def test_delegation_defer_high_pressure(self):
        engine = CoordinationPolicyEngine()
        dec = engine.evaluate_delegation(
            AgentType.RESEARCH, AgentType.DRAFTER,
            workspace_id="ws-1", token_pressure=0.95,
        )
        assert dec.outcome == "defer"

    def test_delegation_deny_low_continuity(self):
        engine = CoordinationPolicyEngine()
        dec = engine.evaluate_delegation(
            AgentType.RESEARCH, AgentType.DRAFTER,
            workspace_id="ws-1", semantic_continuity=0.1, delegation_depth=1,
        )
        assert dec.outcome == "deny"

    def test_provider_routing_selects_best(self):
        engine = CoordinationPolicyEngine()
        dec = engine.evaluate_provider_routing(
            AgentType.RESEARCH, workspace_id="ws-1",
            available_providers=["claude", "openai", "gemini"],
            provider_quality_history={"claude": 0.92, "openai": 0.85, "gemini": 0.88},
        )
        assert dec.outcome == "claude"

    def test_provider_routing_filters_low_quality(self):
        engine = CoordinationPolicyEngine()
        dec = engine.evaluate_provider_routing(
            AgentType.RESEARCH, workspace_id="ws-1",
            available_providers=["claude", "low_provider"],
            provider_quality_history={"claude": 0.9, "low_provider": 0.3},
        )
        assert dec.outcome == "claude"

    def test_token_budget_normal(self):
        engine = CoordinationPolicyEngine()
        dec = engine.evaluate_token_budget(
            AgentType.RESEARCH, workspace_id="ws-1",
            base_budget=4000, token_pressure=0.5,
        )
        # Research has ratio 1.15
        assert int(dec.outcome) > 4000

    def test_token_budget_under_pressure(self):
        engine = CoordinationPolicyEngine()
        dec_normal = engine.evaluate_token_budget(
            AgentType.RESEARCH, workspace_id="ws-1",
            base_budget=4000, token_pressure=0.5,
        )
        dec_pressure = engine.evaluate_token_budget(
            AgentType.RESEARCH, workspace_id="ws-1",
            base_budget=4000, token_pressure=0.95,
        )
        assert int(dec_pressure.outcome) < int(dec_normal.outcome)

    def test_projection_refresh_fresh(self):
        engine = CoordinationPolicyEngine()
        dec = engine.evaluate_projection_refresh(
            workspace_id="ws-1", projection_age_seconds=10.0,
            access_count=5, semantic_drift_estimate=0.05,
        )
        assert dec.outcome == "reuse"

    def test_projection_refresh_stale(self):
        engine = CoordinationPolicyEngine()
        dec = engine.evaluate_projection_refresh(
            workspace_id="ws-1", projection_age_seconds=600.0,
            access_count=100,
        )
        assert dec.outcome == "refresh"

    def test_effectiveness_report(self):
        engine = CoordinationPolicyEngine()
        for _ in range(5):
            engine.evaluate_delegation(AgentType.RESEARCH, AgentType.DRAFTER, "ws-1")
        report = engine.get_effectiveness_report()
        assert report.total_decisions == 5
        assert report.effectiveness_ratio > 0.0

    def test_deterministic_decisions(self):
        """Same inputs → same decisions."""
        results = []
        for _ in range(3):
            engine = CoordinationPolicyEngine()
            dec = engine.evaluate_delegation(
                AgentType.RESEARCH, AgentType.DRAFTER,
                workspace_id="ws-1", semantic_continuity=0.6,
            )
            results.append(dec.outcome)
        assert len(set(results)) == 1


# ---------------------------------------------------------------------------
# AdaptiveDelegationEngine
# ---------------------------------------------------------------------------

class TestAdaptiveDelegationEngine:

    def test_selects_highest_affinity(self):
        engine = AdaptiveDelegationEngine()
        result = engine.select_delegation_target(
            source_type=AgentType.RESEARCH, workspace_id="ws-1",
        )
        # RESEARCH → DRAFTER has highest affinity (0.9)
        assert result.selected_target == AgentType.DRAFTER

    def test_policy_blocks_deep_delegation(self):
        engine = AdaptiveDelegationEngine()
        result = engine.select_delegation_target(
            source_type=AgentType.RESEARCH, workspace_id="ws-1",
            delegation_depth=10,
        )
        assert result.policy_decision.outcome == "deny"

    def test_considers_continuity_history(self):
        engine = AdaptiveDelegationEngine()
        result = engine.select_delegation_target(
            source_type=AgentType.RESEARCH, workspace_id="ws-1",
            semantic_continuity_history={"drafter": 0.95, "critic": 0.3, "tool_agent": 0.1},
        )
        assert result.selected_target == AgentType.DRAFTER

    def test_candidates_sorted_deterministically(self):
        engine = AdaptiveDelegationEngine()
        r1 = engine.select_delegation_target(AgentType.RESEARCH, "ws-1")
        r2 = engine.select_delegation_target(AgentType.RESEARCH, "ws-1")
        assert [c.target_type for c in r1.candidates] == [c.target_type for c in r2.candidates]

    def test_delegation_efficiency_tracking(self):
        engine = AdaptiveDelegationEngine()
        for src in AgentType:
            engine.select_delegation_target(src, "ws-1")
        metrics = engine.get_delegation_efficiency()
        assert metrics["total_evaluations"] == 4
        assert metrics["approval_rate"] > 0.0


# ---------------------------------------------------------------------------
# ProviderRoutingIntelligence
# ---------------------------------------------------------------------------

class TestProviderRoutingIntelligence:

    def test_selects_best_quality(self):
        router = ProviderRoutingIntelligence()
        router.record_quality(AgentType.RESEARCH, "claude", 0.95)
        router.record_quality(AgentType.RESEARCH, "openai", 0.80)
        router.record_quality(AgentType.RESEARCH, "gemini", 0.85)

        result = router.select_provider(
            AgentType.RESEARCH, "ws-1", ["claude", "openai", "gemini"],
        )
        assert result.selected_provider == "claude"

    def test_default_neutral_without_history(self):
        router = ProviderRoutingIntelligence()
        result = router.select_provider(
            AgentType.DRAFTER, "ws-1", ["claude", "openai"],
        )
        # Both default to 0.5, deterministic tiebreak by name
        assert result.selected_provider in ["claude", "openai"]

    def test_quality_history_accumulates(self):
        router = ProviderRoutingIntelligence()
        for q in [0.7, 0.8, 0.9]:
            router.record_quality(AgentType.RESEARCH, "claude", q)

        # Verify internal history has 3 observations
        assert len(router._quality_history["research"]["claude"]) == 3

    def test_routing_determinism(self):
        results = []
        for _ in range(3):
            router = ProviderRoutingIntelligence()
            router.record_quality(AgentType.RESEARCH, "claude", 0.9)
            router.record_quality(AgentType.RESEARCH, "openai", 0.8)
            result = router.select_provider(
                AgentType.RESEARCH, "ws-1", ["claude", "openai"],
            )
            results.append(result.selected_provider)
        assert len(set(results)) == 1


# ---------------------------------------------------------------------------
# ProjectionRefreshManager
# ---------------------------------------------------------------------------

class TestProjectionRefreshManager:

    def test_fresh_projection_reused(self):
        mgr = ProjectionRefreshManager()
        mgr.register_projection("key-1")
        dec = mgr.evaluate_refresh("key-1", estimated_recompile_tokens=500)
        assert dec.action == "reuse"
        assert dec.tokens_saved == 500

    def test_unknown_projection_refreshed(self):
        mgr = ProjectionRefreshManager()
        dec = mgr.evaluate_refresh("unknown-key")
        assert dec.action == "refresh"

    def test_drifted_projection_refreshed(self):
        mgr = ProjectionRefreshManager()
        mgr.register_projection("key-1")
        mgr.update_drift_estimate("key-1", 0.5)  # high drift
        dec = mgr.evaluate_refresh("key-1")
        assert dec.action == "refresh"

    def test_access_tracking(self):
        mgr = ProjectionRefreshManager()
        mgr.register_projection("key-1")
        for _ in range(5):
            mgr.record_access("key-1")
        record = mgr._freshness["key-1"]
        assert record.access_count == 5

    def test_refresh_metrics(self):
        mgr = ProjectionRefreshManager()
        mgr.register_projection("key-1")
        mgr.register_projection("key-2")
        mgr.evaluate_refresh("key-1", estimated_recompile_tokens=100)
        mgr.update_drift_estimate("key-2", 0.5)
        mgr.evaluate_refresh("key-2")

        metrics = mgr.get_refresh_metrics()
        assert metrics["total_evaluations"] == 2
        assert metrics["reuses"] >= 1


# ---------------------------------------------------------------------------
# CoordinationBudgetOptimizer
# ---------------------------------------------------------------------------

class TestCoordinationBudgetOptimizer:

    def test_allocation_respects_priorities(self):
        opt = CoordinationBudgetOptimizer()
        plan = opt.allocate("ws-1", total_budget=4000, agent_types=list(AgentType))

        # Research has highest priority (0.30)
        research_alloc = plan.allocations["research"].allocated_budget
        tool_alloc = plan.allocations["tool_agent"].allocated_budget
        assert research_alloc > tool_alloc

    def test_pressure_reduces_allocation(self):
        opt = CoordinationBudgetOptimizer()
        plan_normal = opt.allocate("ws-1", 4000, list(AgentType), token_pressure=0.3)
        plan_pressure = opt.allocate("ws-1", 4000, list(AgentType), token_pressure=0.95)

        assert plan_pressure.total_allocated < plan_normal.total_allocated

    def test_quality_boost(self):
        opt = CoordinationBudgetOptimizer()
        plan = opt.allocate("ws-1", 4000, list(AgentType),
                            quality_history={"research": 0.95, "drafter": 0.3})

        research = plan.allocations["research"].allocated_budget
        drafter = plan.allocations["drafter"].allocated_budget
        # Research gets quality boost, drafter gets penalty
        assert research > drafter

    def test_budget_metrics(self):
        opt = CoordinationBudgetOptimizer()
        for i in range(3):
            opt.allocate("ws-1", 4000, list(AgentType), token_pressure=i * 0.3)

        metrics = opt.get_budget_metrics()
        assert metrics["total_plans"] == 3
        assert metrics["avg_efficiency_score"] > 0.0

    def test_deterministic_allocation(self):
        plans = []
        for _ in range(3):
            opt = CoordinationBudgetOptimizer()
            plan = opt.allocate("ws-1", 4000, list(AgentType), token_pressure=0.5)
            plans.append(plan.total_allocated)
        assert len(set(plans)) == 1


# ---------------------------------------------------------------------------
# Cross-component integration
# ---------------------------------------------------------------------------

class TestCoordinationIntelligenceIntegration:

    def test_shared_policy_engine(self):
        """All components share a single policy engine."""
        policy = CoordinationPolicyEngine()
        deleg = AdaptiveDelegationEngine(policy)
        router = ProviderRoutingIntelligence(policy)
        refresh = ProjectionRefreshManager(policy)
        budget = CoordinationBudgetOptimizer(policy)

        deleg.select_delegation_target(AgentType.RESEARCH, "ws-1")
        router.select_provider(AgentType.DRAFTER, "ws-1", ["claude"])
        refresh.register_projection("k1")
        refresh.evaluate_refresh("k1")
        budget.allocate("ws-1", 4000, list(AgentType))

        report = policy.get_effectiveness_report()
        # delegation + provider_routing + projection_refresh (budget optimizer is self-contained)
        assert report.total_decisions >= 3
        assert len(report.decisions_by_type) >= 3

    def test_end_to_end_coordination_cycle(self):
        """Full intelligence cycle: route → allocate → delegate → refresh."""
        policy = CoordinationPolicyEngine()
        router = ProviderRoutingIntelligence(policy)
        budget = CoordinationBudgetOptimizer(policy)
        deleg = AdaptiveDelegationEngine(policy)
        refresh = ProjectionRefreshManager(policy)

        # 1. Route provider
        router.record_quality(AgentType.RESEARCH, "claude", 0.9)
        route = router.select_provider(AgentType.RESEARCH, "ws-1", ["claude", "openai"])
        assert route.selected_provider == "claude"

        # 2. Allocate budget
        plan = budget.allocate("ws-1", 4000, list(AgentType))
        assert plan.total_allocated > 0

        # 3. Delegate
        result = deleg.select_delegation_target(AgentType.RESEARCH, "ws-1")
        assert result.policy_decision.outcome == "allow"

        # 4. Check projection freshness
        refresh.register_projection("proj-1")
        dec = refresh.evaluate_refresh("proj-1", estimated_recompile_tokens=300)
        assert dec.action == "reuse"

        # Verify all decisions tracked (provider_routing + delegation + projection_refresh)
        assert policy.get_effectiveness_report().total_decisions >= 3

    def test_replay_determinism_full_cycle(self):
        """Full cycle produces identical policy logs on replay."""
        logs = []
        for _ in range(3):
            policy = CoordinationPolicyEngine()
            router = ProviderRoutingIntelligence(policy)
            router.record_quality(AgentType.RESEARCH, "claude", 0.9)
            router.select_provider(AgentType.RESEARCH, "ws-1", ["claude", "openai"])

            deleg = AdaptiveDelegationEngine(policy)
            deleg.select_delegation_target(AgentType.RESEARCH, "ws-1")

            budget = CoordinationBudgetOptimizer(policy)
            budget.allocate("ws-1", 4000, list(AgentType), token_pressure=0.5)

            decisions = policy.get_decision_log()
            logs.append([(d["outcome"], d["rationale"]) for d in decisions])

        assert logs[0] == logs[1] == logs[2]
