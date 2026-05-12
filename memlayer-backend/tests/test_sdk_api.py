"""Phase 8 — SDK & Runtime APIs test suite.

Validates:
- MemLayerSDK: unified entry point, workspace → compile → coordinate → replay
- WorkspaceAPI: lifecycle, memory management, snapshots, diagnostics
- ViewAPI: generation, caching, comparison, diagnostics
- CoordinationAPI: execution, policy, delegation, history
- ReplayAPI: determinism verification, comparison, diagnostics
- TelemetryAPI: analytics, latency, providers, export
- ProviderAdapter: capabilities, budget validation, cost estimation
- End-to-end SDK integration and replay determinism
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import json

import pytest

from app.sdk import (
    MemLayerSDK,
    WorkspaceAPI,
    WorkspaceConfig,
    ViewAPI,
    CoordinationAPI,
    CoordinationRequest,
    ReplayAPI,
    TelemetryAPI,
    ProviderAdapter,
    PROVIDER_REGISTRY,
)


# ---------------------------------------------------------------------------
# Test memory
# ---------------------------------------------------------------------------

@dataclass
class SDKMemory:
    id: str
    raw_content: str
    importance_score: float
    timestamp: datetime
    embedding: list

    def __str__(self) -> str:
        return self.raw_content


def _test_memories(count: int = 15):
    return [
        SDKMemory(
            id=f"sdk-m-{i:03d}",
            raw_content=f"Entity{i} evidence source reference step contradiction {i}.",
            importance_score=0.5 + (i % 4) * 0.1,
            timestamp=datetime.now(timezone.utc),
            embedding=[(i + j) / 100.0 for j in range(12)],
        )
        for i in range(count)
    ]


# ---------------------------------------------------------------------------
# ProviderAdapter
# ---------------------------------------------------------------------------

class TestProviderAdapter:

    def test_list_providers(self):
        adapter = ProviderAdapter()
        providers = adapter.list_providers()
        assert "claude" in providers
        assert "openai" in providers
        assert "gemini" in providers

    def test_capabilities(self):
        adapter = ProviderAdapter()
        caps = adapter.get_capabilities("claude")
        assert caps is not None
        assert caps.max_context_tokens == 200000

    def test_budget_validation_ok(self):
        adapter = ProviderAdapter()
        result = adapter.validate_budget("claude", 4000)
        assert result["valid"] is True

    def test_budget_validation_exceeds(self):
        adapter = ProviderAdapter()
        result = adapter.validate_budget("openai", 500000)
        assert result["valid"] is False

    def test_cost_estimation(self):
        adapter = ProviderAdapter()
        cost = adapter.estimate_cost("claude", input_tokens=1000, output_tokens=500)
        assert cost["total_cost"] > 0

    def test_optimal_provider_for_budget(self):
        adapter = ProviderAdapter()
        provider = adapter.optimal_provider_for_budget(4000)
        assert provider in ["claude", "openai", "gemini"]


# ---------------------------------------------------------------------------
# WorkspaceAPI
# ---------------------------------------------------------------------------

class TestWorkspaceAPI:

    def test_create_workspace(self):
        api = WorkspaceAPI()
        snap = api.create_workspace(WorkspaceConfig(workspace_id="ws-test"))
        assert snap.workspace_id == "ws-test"
        assert snap.memory_count == 0

    def test_add_memories(self):
        api = WorkspaceAPI()
        api.create_workspace(WorkspaceConfig(workspace_id="ws-test"))
        snap = api.add_memories("ws-test", _test_memories(10))
        assert snap.memory_count == 10

    def test_get_workspace(self):
        api = WorkspaceAPI()
        api.create_workspace(WorkspaceConfig(workspace_id="ws-test"))
        ws = api.get_workspace("ws-test")
        assert ws is not None
        assert ws["workspace_id"] == "ws-test"

    def test_update_config(self):
        api = WorkspaceAPI()
        api.create_workspace(WorkspaceConfig(workspace_id="ws-test"))
        snap = api.update_config("ws-test", provider="openai", token_budget=8000)
        assert snap.provider == "openai"
        assert snap.token_budget == 8000  # custom budget

    def test_diagnostics(self):
        api = WorkspaceAPI()
        api.create_workspace(WorkspaceConfig(workspace_id="ws-test"))
        api.add_memories("ws-test", _test_memories(5))
        diag = api.get_diagnostics("ws-test")
        assert diag["memory_count"] == 5
        assert diag["snapshot_count"] >= 2

    def test_list_workspaces(self):
        api = WorkspaceAPI()
        api.create_workspace(WorkspaceConfig(workspace_id="ws-a"))
        api.create_workspace(WorkspaceConfig(workspace_id="ws-b"))
        workspaces = api.list_workspaces()
        assert len(workspaces) == 2

    def test_nonexistent_workspace_raises(self):
        api = WorkspaceAPI()
        with pytest.raises(ValueError):
            api.add_memories("nonexistent", [])


# ---------------------------------------------------------------------------
# ViewAPI
# ---------------------------------------------------------------------------

class TestViewAPI:

    def test_generate_single_view(self):
        sdk = MemLayerSDK()
        ws = sdk.create_workspace(workspace_id="ws-view")
        sdk.add_memories("ws-view", _test_memories())

        result = sdk.generate_view("ws-view", "test query", view_type="research")
        assert result.view_type == "research"
        assert result.projection_checksum != ""
        assert result.token_count > 0

    def test_generate_all_views(self):
        sdk = MemLayerSDK()
        ws = sdk.create_workspace(workspace_id="ws-views")
        sdk.add_memories("ws-views", _test_memories())

        views = sdk.generate_views("ws-views", "test query")
        assert len(views) == 4
        assert "research" in views

    def test_compare_projections(self):
        sdk = MemLayerSDK()
        ws = sdk.create_workspace(workspace_id="ws-cmp")
        sdk.add_memories("ws-cmp", _test_memories())
        state = sdk.compile("ws-cmp", "test query")

        result = sdk.views.compare_projections(state, "claude", "openai")
        assert result.view_type == "research"
        assert isinstance(result.quality_delta, float)

    def test_view_diagnostics(self):
        sdk = MemLayerSDK()
        ws = sdk.create_workspace(workspace_id="ws-diag")
        sdk.add_memories("ws-diag", _test_memories())
        sdk.generate_views("ws-diag", "test query")

        diag = sdk.views.get_diagnostics()
        assert "context_bus" in diag
        assert "reuse_metrics" in diag


# ---------------------------------------------------------------------------
# CoordinationAPI
# ---------------------------------------------------------------------------

class TestCoordinationAPI:

    def test_coordinated_execution(self):
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-coord")
        sdk.add_memories("ws-coord", _test_memories())

        result = sdk.coordinate("ws-coord", "evaluate agents")
        assert result.success is True
        assert result.agent_count == 4
        assert result.total_tokens_consumed > 0

    def test_single_agent_execution(self):
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-single")
        sdk.add_memories("ws-single", _test_memories())
        state = sdk.compile("ws-single", "test")

        result = sdk.coordination.execute_single_agent(state, "research")
        assert result["success"] is True
        assert result["agent_type"] == "research"

    def test_coordination_with_delegation(self):
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-deleg")
        sdk.add_memories("ws-deleg", _test_memories())

        result = sdk.coordinate(
            "ws-deleg", "test with delegation",
            delegation_chain=[
                ("research", "drafter", "synthesize"),
                ("drafter", "critic", "review"),
            ],
        )
        assert result.success is True
        assert result.delegation_count == 2

    def test_coordination_history(self):
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-hist")
        sdk.add_memories("ws-hist", _test_memories())

        for _ in range(3):
            sdk.coordinate("ws-hist", "test")

        history = sdk.coordination.get_coordination_history()
        assert len(history) == 3

    def test_policy_decisions_tracked(self):
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-policy")
        sdk.add_memories("ws-policy", _test_memories())
        sdk.coordinate("ws-policy", "test")

        # No direct policy calls through coordination yet, but structure is ready
        effectiveness = sdk.coordination.get_policy_effectiveness()
        assert "total_decisions" in effectiveness


# ---------------------------------------------------------------------------
# ReplayAPI
# ---------------------------------------------------------------------------

class TestReplayAPI:

    def test_replay_determinism(self):
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-replay")
        sdk.add_memories("ws-replay", _test_memories())

        sdk.coordinate("ws-replay", "test query")
        result = sdk.replay_last("ws-replay", "test query")
        assert result is not None
        assert result.is_deterministic is True
        assert result.checksum_match is True

    def test_replay_view(self):
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-rv")
        sdk.add_memories("ws-rv", _test_memories())
        state = sdk.compile("ws-rv", "test")

        result = sdk.replay.replay_view(state, "research")
        assert "checksum" in result
        assert result["quality"] > 0.0

    def test_compare_runs(self):
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-cmp2")
        sdk.add_memories("ws-cmp2", _test_memories())
        state = sdk.compile("ws-cmp2", "test")

        report1 = sdk.coordination._runtime.execute_coordinated(state, provider="claude")
        report2 = sdk.coordination._runtime.execute_coordinated(state, provider="claude")

        comparison = sdk.replay.compare_runs(report1, report2)
        assert comparison.match_ratio == 1.0
        assert len(comparison.divergences) == 0

    def test_replay_diagnostics(self):
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-rd")
        sdk.add_memories("ws-rd", _test_memories())

        sdk.coordinate("ws-rd", "test")
        sdk.replay_last("ws-rd", "test")

        diag = sdk.replay.get_replay_diagnostics()
        assert diag["total_replays"] >= 1
        assert diag["determinism_ratio"] == 1.0


# ---------------------------------------------------------------------------
# TelemetryAPI
# ---------------------------------------------------------------------------

class TestTelemetryAPI:

    def test_token_analytics(self):
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-telem")
        sdk.add_memories("ws-telem", _test_memories())

        for _ in range(3):
            sdk.coordinate("ws-telem", "test")

        analytics = sdk.get_token_savings()
        assert analytics["total_runs"] == 3
        assert analytics["total_tokens_consumed"] > 0

    def test_latency_profile(self):
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-lat")
        sdk.add_memories("ws-lat", _test_memories())
        sdk.coordinate("ws-lat", "test")

        profile = sdk.telemetry.get_latency_profile()
        assert profile["total_runs"] >= 1
        assert profile["avg_duration_ms"] >= 0

    def test_provider_benchmark(self):
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-pb")
        sdk.add_memories("ws-pb", _test_memories())

        for provider in ["claude", "openai", "gemini"]:
            sdk.coordinate("ws-pb", "test", provider=provider)

        benchmark = sdk.telemetry.get_provider_benchmark()
        assert len(benchmark["providers"]) == 3

    def test_coordination_traces(self):
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-ct")
        sdk.add_memories("ws-ct", _test_memories())
        sdk.coordinate("ws-ct", "test")

        traces = sdk.telemetry.get_coordination_traces()
        assert len(traces) >= 1

    def test_runtime_summary(self):
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-sum")
        sdk.add_memories("ws-sum", _test_memories())
        sdk.coordinate("ws-sum", "test")

        summary = sdk.get_telemetry()
        assert "token_analytics" in summary
        assert "latency" in summary
        assert "providers" in summary

    def test_export_telemetry(self, tmp_path):
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-exp")
        sdk.add_memories("ws-exp", _test_memories())
        sdk.coordinate("ws-exp", "test")

        out = str(tmp_path / "telemetry.json")
        sdk.telemetry.export_telemetry(out)
        data = json.loads(open(out).read())
        assert "token_analytics" in data


# ---------------------------------------------------------------------------
# End-to-end SDK integration
# ---------------------------------------------------------------------------

class TestSDKIntegration:

    def test_full_lifecycle(self):
        """workspace → memories → compile → views → coordinate → replay → telemetry."""
        sdk = MemLayerSDK()

        # 1. Workspace
        ws = sdk.create_workspace(workspace_id="ws-full")
        assert ws.workspace_id == "ws-full"

        # 2. Memories
        sdk.add_memories("ws-full", _test_memories(20))

        # 3. Views
        views = sdk.generate_views("ws-full", "full lifecycle test")
        assert len(views) == 4

        # 4. Coordination
        result = sdk.coordinate("ws-full", "full lifecycle test")
        assert result.success is True
        assert result.total_tokens_consumed > 0

        # 5. Replay
        replay = sdk.replay_last("ws-full", "full lifecycle test")
        assert replay is not None
        assert replay.is_deterministic is True

        # 6. Telemetry
        telemetry = sdk.get_telemetry()
        assert telemetry["token_analytics"]["total_runs"] >= 1

    def test_multi_provider_lifecycle(self):
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-mp")
        sdk.add_memories("ws-mp", _test_memories())

        for provider in ["claude", "openai", "gemini"]:
            result = sdk.coordinate("ws-mp", "multi-provider", provider=provider)
            assert result.success is True
            assert result.provider == provider

        benchmark = sdk.telemetry.get_provider_benchmark()
        assert len(benchmark["providers"]) == 3

    def test_sdk_diagnostics(self):
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-diag")
        sdk.add_memories("ws-diag", _test_memories())
        sdk.coordinate("ws-diag", "diagnostics test")

        diag = sdk.get_diagnostics()
        assert "workspaces" in diag
        assert "providers" in diag
        assert "coordination" in diag
        assert "views" in diag
        assert "replay" in diag

    def test_deterministic_sdk_operations(self):
        """Same SDK operations produce identical results."""
        results = []
        for _ in range(3):
            sdk = MemLayerSDK()
            sdk.create_workspace(workspace_id="ws-det")
            sdk.add_memories("ws-det", _test_memories(10))
            result = sdk.coordinate("ws-det", "determinism test")
            results.append(result.total_tokens_consumed)

        assert len(set(results)) == 1

    def test_serialization_stability(self):
        """All API results serialize cleanly."""
        sdk = MemLayerSDK()
        sdk.create_workspace(workspace_id="ws-ser")
        sdk.add_memories("ws-ser", _test_memories())

        result = sdk.coordinate("ws-ser", "serialization")
        payload = json.dumps(result.to_dict(), default=str)
        parsed = json.loads(payload)
        assert parsed["success"] is True

        telemetry = sdk.get_telemetry()
        payload2 = json.dumps(telemetry, default=str)
        assert "token_analytics" in payload2
