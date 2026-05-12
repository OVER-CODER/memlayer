"""
Tests for Phase 5B Runtime Validation Infrastructure.

Tests for integrated runtime, replay engine, and failure detection.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock

from app.runtime import (
    IntegratedRuntimeSystem,
    UnifiedCognitionTrace,
    RuntimeReplayEngine,
    ReplayableTrace,
    EmergentFailureDetector,
    FailureType,
    FailureSeverity,
    LongHorizonStressHarness,
    StressScenario,
    StressTestRun,
)

from app.compiler.adaptive_assembly_pipeline import (
    AdaptiveAssemblyPipeline,
    AdaptiveAssemblyResult,
    PipelineStageMetrics,
    PipelineStage,
)


class TestIntegratedRuntimeSystem:
    """Test end-to-end runtime integration."""

    def test_initialization(self):
        """Test integrated runtime initialization."""
        # Create mock pipeline
        mock_pipeline = MagicMock(spec=AdaptiveAssemblyPipeline)

        runtime = IntegratedRuntimeSystem(mock_pipeline)

        assert runtime.pipeline is not None
        assert runtime.trace_service is not None
        assert runtime.token_analytics is not None
        assert runtime.latency_profiler is not None
        assert runtime.drift_analyzer is not None
        assert runtime.benchmarking_service is not None

    def test_execution_with_telemetry(self):
        """Test execution with complete telemetry integration."""
        # Create mock pipeline with result
        mock_pipeline = MagicMock(spec=AdaptiveAssemblyPipeline)
        mock_result = AdaptiveAssemblyResult(
            query="Test query",
            provider="claude",
            compression_mode="balanced",
            compiled_context="Compiled context here",
            reasoning_context="Reasoning",
            semantic_memories="Memories",
            workspace_summary="Workspace",
            quality_score=Mock(overall_quality=Mock(return_value=0.9)),
            semantic_retention=0.88,
            token_efficiency=0.85,
            total_duration_ms=50.0,
            stage_metrics=[
                PipelineStageMetrics(
                    stage=PipelineStage.RANKING,
                    duration_ms=10.0,
                    input_count=100,
                    output_count=50,
                ),
                PipelineStageMetrics(
                    stage=PipelineStage.COMPRESSION,
                    duration_ms=20.0,
                    input_count=50,
                    output_count=25,
                ),
            ],
        )
        mock_pipeline.execute.return_value = mock_result

        runtime = IntegratedRuntimeSystem(mock_pipeline)

        # Execute with telemetry
        unified_trace = runtime.execute_with_telemetry(
            query="Test query",
            memories=["mem1", "mem2", "mem3"],
            token_budget=4000,
            provider="claude",
            compression_mode="balanced",
            query_type="general",
        )

        assert unified_trace is not None
        assert unified_trace.success
        assert unified_trace.quality_score > 0
        assert unified_trace.semantic_retention > 0
        assert unified_trace.token_efficiency > 0
        assert unified_trace.trace_id in runtime.replay_engine.stored_traces
        assert len(runtime.evolution_tracker.all_data_points) >= 6

    def test_runtime_statistics(self):
        """Test runtime statistics calculation."""
        mock_pipeline = MagicMock(spec=AdaptiveAssemblyPipeline)
        mock_result = AdaptiveAssemblyResult(
            query="Test",
            provider="claude",
            compression_mode="balanced",
            compiled_context="Context",
            reasoning_context="",
            semantic_memories="",
            workspace_summary="",
            quality_score=Mock(overall_quality=Mock(return_value=0.9)),
            semantic_retention=0.88,
            token_efficiency=0.85,
            total_duration_ms=50.0,
            stage_metrics=[],
        )
        mock_pipeline.execute.return_value = mock_result

        runtime = IntegratedRuntimeSystem(mock_pipeline)

        # Execute multiple times
        for i in range(3):
            runtime.execute_with_telemetry(
                query=f"Query {i}",
                memories=["mem1"],
                token_budget=4000,
                provider="claude",
            )

        stats = runtime.get_runtime_statistics()

        assert stats["total_executions"] == 3
        assert stats["successful_executions"] == 3
        assert stats["success_rate"] == 1.0


class TestRuntimeReplayEngine:
    """Test replay engine functionality."""

    def test_store_and_retrieve_trace(self):
        """Test storing and retrieving traces."""
        engine = RuntimeReplayEngine()

        trace = ReplayableTrace(
            trace_id="trace-1",
            timestamp=datetime.now(timezone.utc),
            query="Test query",
            query_type="general",
            provider="claude",
            compression_mode="balanced",
            token_budget=4000,
            memories_count=10,
        )

        engine.store_trace(trace)
        retrieved = engine.get_trace("trace-1")

        assert retrieved is not None
        assert retrieved.trace_id == "trace-1"
        assert retrieved.query == "Test query"

    def test_trace_integrity_validation(self):
        """Test trace integrity validation."""
        engine = RuntimeReplayEngine()

        trace = ReplayableTrace(
            trace_id="trace-2",
            timestamp=datetime.now(timezone.utc),
            query="Integrity test",
            query_type="general",
            provider="openai",
            compression_mode="aggressive",
            token_budget=8000,
            memories_count=20,
        )

        engine.store_trace(trace)

        # Check integrity
        is_valid = engine.validate_trace_integrity("trace-2")
        assert is_valid

    def test_trace_comparison(self):
        """Test comparing two traces."""
        engine = RuntimeReplayEngine()

        trace1 = ReplayableTrace(
            trace_id="trace-1",
            timestamp=datetime.now(timezone.utc),
            query="Query",
            query_type="general",
            provider="claude",
            compression_mode="balanced",
            token_budget=4000,
            memories_count=10,
            quality_score=0.9,
            semantic_retention=0.88,
            token_efficiency=0.85,
        )

        trace2 = ReplayableTrace(
            trace_id="trace-2",
            timestamp=datetime.now(timezone.utc),
            query="Query",
            query_type="general",
            provider="claude",
            compression_mode="balanced",
            token_budget=4000,
            memories_count=10,
            quality_score=0.91,  # Very similar
            semantic_retention=0.87,
            token_efficiency=0.86,
        )

        engine.store_trace(trace1)
        engine.store_trace(trace2)

        comparison = engine.compare_traces("trace-1", "trace-2")

        assert comparison["parameters_match"] is True
        assert comparison["similarity_score"] > 80

    def test_trace_replay_simulation(self):
        """Test trace replay simulation."""
        engine = RuntimeReplayEngine()

        trace = ReplayableTrace(
            trace_id="trace-replay",
            timestamp=datetime.now(timezone.utc),
            query="Replay test",
            query_type="general",
            provider="claude",
            compression_mode="balanced",
            token_budget=4000,
            memories_count=10,
            quality_score=0.9,
            semantic_retention=0.88,
            token_efficiency=0.85,
        )

        engine.store_trace(trace)

        # Replay with no perturbation
        replay_result = engine.simulate_replay("trace-replay", perturbation_factor=0.0)

        assert replay_result.replayed_successfully
        assert replay_result.fidelity_score >= 95

    def test_replay_statistics(self):
        """Test replay statistics."""
        engine = RuntimeReplayEngine()

        trace = ReplayableTrace(
            trace_id="trace-stats",
            timestamp=datetime.now(timezone.utc),
            query="Stats test",
            query_type="general",
            provider="claude",
            compression_mode="balanced",
            token_budget=4000,
            memories_count=10,
            quality_score=0.9,
            semantic_retention=0.88,
        )

        engine.store_trace(trace)

        # Do multiple replays
        for i in range(3):
            engine.simulate_replay(f"trace-stats", perturbation_factor=0.0)

        stats = engine.get_replay_statistics()

        assert stats["total_replays"] == 3
        assert stats["successful_replays"] >= 2
        assert stats["stored_traces"] == 1


class TestEmergentFailureDetector:
    """Test emergent failure detection."""

    def test_semantic_collapse_detection(self):
        """Test detection of semantic collapse."""
        detector = EmergentFailureDetector()

        failure = detector.detect_semantic_collapse(
            failure_id="fail-1",
            query="Test query",
            provider="claude",
            compression_mode="aggressive",
            current_semantic_density=0.40,  # 60% degradation (exceeds 50% for CATASTROPHIC)
            previous_semantic_density=1.0,
            cycle_number=3,
        )

        assert failure is not None
        assert failure.failure_type == FailureType.SEMANTIC_COLLAPSE
        assert failure.severity == FailureSeverity.CATASTROPHIC

    def test_entity_erosion_detection(self):
        """Test detection of entity erosion."""
        detector = EmergentFailureDetector()

        failure = detector.detect_entity_erosion(
            failure_id="fail-2",
            query="Test query",
            provider="openai",
            previous_entity_count=100,
            current_entity_count=60,  # 40% loss
            current_preservation_ratio=0.60,
            cycle_number=2,
        )

        assert failure is not None
        assert failure.failure_type == FailureType.ENTITY_EROSION
        assert failure.entity_preservation == 0.60

    def test_reasoning_continuity_loss_detection(self):
        """Test detection of reasoning continuity loss."""
        detector = EmergentFailureDetector()

        failure = detector.detect_reasoning_continuity_loss(
            failure_id="fail-3",
            query="Complex reasoning query",
            provider="claude",
            previous_continuity=0.95,
            current_continuity=0.70,  # 26% loss
            cycle_number=2,
        )

        assert failure is not None
        assert failure.failure_type == FailureType.REASONING_CONTINUITY_LOSS
        assert failure.severity == FailureSeverity.ERROR

    def test_token_explosion_detection(self):
        """Test detection of token explosion."""
        detector = EmergentFailureDetector()

        failure = detector.detect_token_explosion(
            failure_id="fail-4",
            query="Test",
            provider="gemini",
            previous_token_count=1000,
            current_token_count=2000,  # 100% growth
            token_budget=4000,
            cycle_number=3,
        )

        assert failure is not None
        assert failure.failure_type == FailureType.TOKEN_EXPLOSION
        assert failure.severity == FailureSeverity.ERROR

    def test_provider_instability_detection(self):
        """Test detection of provider instability."""
        detector = EmergentFailureDetector()

        quality_scores = [0.85, 0.25, 0.90, 0.20, 0.88]  # High variance (> 0.2 std dev)

        failure = detector.detect_provider_instability(
            failure_id="fail-5",
            provider="openai",
            query_type="general",
            quality_scores=quality_scores,
        )

        assert failure is not None
        assert failure.failure_type == FailureType.PROVIDER_INSTABILITY

    def test_allocation_drift_detection(self):
        """Test detection of allocation drift."""
        detector = EmergentFailureDetector()

        planned = {
            "reasoning_context": 1000,
            "semantic_memories": 2000,
            "workspace_summary": 500,
        }

        actual = {
            "reasoning_context": 500,  # 50% drift
            "semantic_memories": 2500,
            "workspace_summary": 200,
        }

        failure = detector.detect_allocation_drift(
            failure_id="fail-6",
            query="Test",
            provider="claude",
            planned_allocation=planned,
            actual_allocation=actual,
            cycle_number=1,
        )

        assert failure is not None
        assert failure.failure_type == FailureType.ALLOCATION_DRIFT

    def test_failure_report(self):
        """Test failure reporting."""
        detector = EmergentFailureDetector()

        # Generate multiple failures
        detector.detect_semantic_collapse(
            "fail-1", "Query", "claude", "balanced", 0.6, 1.0
        )
        detector.detect_token_explosion("fail-2", "Query", "claude", 1000, 2000, 4000)

        report = detector.get_failure_report()

        assert report["total_failures"] == 2
        assert len(report["by_type"]) >= 2


class TestLongHorizonStressHarness:
    """Test long-horizon stress harness functionality."""

    def test_stress_harness_initialization(self):
        """Test stress harness initialization."""
        mock_pipeline = MagicMock(spec=AdaptiveAssemblyPipeline)
        runtime = IntegratedRuntimeSystem(mock_pipeline)
        harness = LongHorizonStressHarness(runtime)

        assert harness.runtime is not None
        assert harness.failure_detector is not None
        assert len(harness.test_runs) == 0

    def test_stress_scenario_creation(self):
        """Test stress scenario creation."""
        scenario = StressScenario(
            scenario_id="test-1",
            scenario_name="Test Scenario",
            description="Test scenario for unit testing",
            num_turns=50,
            num_memories=25,
            memory_noise_level=0.1,
            recursive_compression_cycles=2,
            token_budget=4000,
            token_pressure_level=0.8,
            query_complexity="moderate",
            query_diversity=0.5,
        )

        assert scenario.scenario_id == "test-1"
        assert scenario.num_turns == 50
        assert scenario.num_memories == 25
        assert scenario.memory_noise_level == 0.1

    def test_stress_scenario_to_dict(self):
        """Test converting scenario to dictionary."""
        scenario = StressScenario(
            scenario_id="test-2",
            scenario_name="Dict Test Scenario",
            description="Test scenario conversion",
            num_turns=100,
            num_memories=50,
        )

        scenario_dict = scenario.to_dict()

        assert scenario_dict["scenario_id"] == "test-2"
        assert scenario_dict["num_turns"] == 100
        assert scenario_dict["num_memories"] == 50
        assert isinstance(scenario_dict, dict)

    def test_stress_test_run_creation(self):
        """Test stress test run creation."""
        scenario = StressScenario(
            scenario_id="test-run",
            scenario_name="Test Run",
            description="Test run scenario",
        )

        run = StressTestRun(
            run_id="run-1",
            scenario=scenario,
        )

        assert run.run_id == "run-1"
        assert run.scenario == scenario
        assert run.total_turns == 0
        assert run.successful_turns == 0
        assert run.failed_turns == 0
        assert run.stability_score == 0.0

    def test_stress_test_run_to_dict(self):
        """Test converting stress test run to dictionary."""
        scenario = StressScenario(
            scenario_id="dict-test",
            scenario_name="Dict Test",
            description="Dict conversion test",
        )

        run = StressTestRun(
            run_id="run-dict-1",
            scenario=scenario,
            total_turns=50,
            successful_turns=48,
            failed_turns=2,
            avg_quality_score=0.87,
            stability_score=85.0,
        )

        run_dict = run.to_dict()

        assert run_dict["run_id"] == "run-dict-1"
        assert run_dict["total_turns"] == 50
        assert run_dict["successful_turns"] == 48
        assert run_dict["avg_quality_score"] == 0.87
        assert "success_rate" in run_dict

    def test_run_scenario_basic(self):
        """Test running a basic stress scenario."""
        mock_pipeline = MagicMock(spec=AdaptiveAssemblyPipeline)
        mock_result = AdaptiveAssemblyResult(
            query="Test query",
            provider="claude",
            compression_mode="balanced",
            compiled_context="Context",
            reasoning_context="Reasoning",
            semantic_memories="Memories",
            workspace_summary="Workspace",
            quality_score=Mock(overall_quality=Mock(return_value=0.9)),
            semantic_retention=0.88,
            token_efficiency=0.85,
            total_duration_ms=50.0,
            stage_metrics=[],
        )
        mock_pipeline.execute.return_value = mock_result

        runtime = IntegratedRuntimeSystem(mock_pipeline)
        harness = LongHorizonStressHarness(runtime)

        scenario = StressScenario(
            scenario_id="basic-stress",
            scenario_name="Basic Stress",
            description="Basic stress test",
            num_turns=10,
            num_memories=5,
        )

        run = harness.run_scenario(scenario)

        assert run.run_id is not None
        assert run.total_turns == 10
        assert run.successful_turns > 0  # Most should succeed with mock
        assert run.avg_quality_score > 0

    def test_scenario_quality_degradation_tracking(self):
        """Test quality degradation tracking across scenario."""
        mock_pipeline = MagicMock(spec=AdaptiveAssemblyPipeline)

        # Simulate degrading quality scores
        quality_scores = [0.95, 0.92, 0.87, 0.82, 0.75]

        def side_effect(*args, **kwargs):
            turn = mock_pipeline.execute.call_count - 1
            if turn < len(quality_scores):
                return AdaptiveAssemblyResult(
                    query="Query",
                    provider="claude",
                    compression_mode="balanced",
                    compiled_context="Context",
                    reasoning_context="Reasoning",
                    semantic_memories="Memories",
                    workspace_summary="Workspace",
                    quality_score=Mock(
                        overall_quality=Mock(return_value=quality_scores[turn])
                    ),
                    semantic_retention=0.88,
                    token_efficiency=0.85,
                    total_duration_ms=50.0,
                    stage_metrics=[],
                )
            return AdaptiveAssemblyResult(
                query="Query",
                provider="claude",
                compression_mode="balanced",
                compiled_context="Context",
                reasoning_context="Reasoning",
                semantic_memories="Memories",
                workspace_summary="Workspace",
                quality_score=Mock(overall_quality=Mock(return_value=0.9)),
                semantic_retention=0.88,
                token_efficiency=0.85,
                total_duration_ms=50.0,
                stage_metrics=[],
            )

        mock_pipeline.execute.side_effect = side_effect

        runtime = IntegratedRuntimeSystem(mock_pipeline)
        harness = LongHorizonStressHarness(runtime)

        scenario = StressScenario(
            scenario_id="degrad-test",
            scenario_name="Degradation Test",
            description="Test quality degradation",
            num_turns=5,
            num_memories=5,
        )

        run = harness.run_scenario(scenario)

        # Check that degradation was detected
        assert run.quality_degradation_rate >= 0

    def test_scenario_with_memory_noise(self):
        """Test scenario execution with memory noise."""
        mock_pipeline = MagicMock(spec=AdaptiveAssemblyPipeline)
        mock_result = AdaptiveAssemblyResult(
            query="Test query",
            provider="claude",
            compression_mode="balanced",
            compiled_context="Context",
            reasoning_context="Reasoning",
            semantic_memories="Memories",
            workspace_summary="Workspace",
            quality_score=Mock(overall_quality=Mock(return_value=0.9)),
            semantic_retention=0.88,
            token_efficiency=0.85,
            total_duration_ms=50.0,
            stage_metrics=[],
        )
        mock_pipeline.execute.return_value = mock_result

        runtime = IntegratedRuntimeSystem(mock_pipeline)
        harness = LongHorizonStressHarness(runtime)

        scenario = StressScenario(
            scenario_id="noise-test",
            scenario_name="Memory Noise Test",
            description="Test with memory noise",
            num_turns=10,
            num_memories=10,
            memory_noise_level=0.2,  # 20% noise
        )

        run = harness.run_scenario(scenario)

        assert run.total_turns == 10
        assert run.successful_turns > 0

    def test_scenario_with_recursive_compression(self):
        """Test scenario with recursive compression cycles."""
        mock_pipeline = MagicMock(spec=AdaptiveAssemblyPipeline)
        mock_result = AdaptiveAssemblyResult(
            query="Test query",
            provider="claude",
            compression_mode="balanced",
            compiled_context="Context",
            reasoning_context="Reasoning",
            semantic_memories="Memories",
            workspace_summary="Workspace",
            quality_score=Mock(overall_quality=Mock(return_value=0.9)),
            semantic_retention=0.88,
            token_efficiency=0.85,
            total_duration_ms=50.0,
            stage_metrics=[],
        )
        mock_pipeline.execute.return_value = mock_result

        runtime = IntegratedRuntimeSystem(mock_pipeline)
        harness = LongHorizonStressHarness(runtime)

        scenario = StressScenario(
            scenario_id="recursive-test",
            scenario_name="Recursive Compression Test",
            description="Test with recursive compression",
            num_turns=20,
            num_memories=10,
            recursive_compression_cycles=3,
            memory_growth_factor=1.5,
        )

        run = harness.run_scenario(scenario)

        assert run.total_turns == 20
        assert run.successful_turns > 0

    def test_scenario_with_provider_switching(self):
        """Test scenario with provider switching."""
        mock_pipeline = MagicMock(spec=AdaptiveAssemblyPipeline)
        mock_result = AdaptiveAssemblyResult(
            query="Test query",
            provider="claude",
            compression_mode="balanced",
            compiled_context="Context",
            reasoning_context="Reasoning",
            semantic_memories="Memories",
            workspace_summary="Workspace",
            quality_score=Mock(overall_quality=Mock(return_value=0.9)),
            semantic_retention=0.88,
            token_efficiency=0.85,
            total_duration_ms=50.0,
            stage_metrics=[],
        )
        mock_pipeline.execute.return_value = mock_result

        runtime = IntegratedRuntimeSystem(mock_pipeline)
        harness = LongHorizonStressHarness(runtime)

        scenario = StressScenario(
            scenario_id="switch-test",
            scenario_name="Provider Switching Test",
            description="Test with provider switching",
            num_turns=15,
            num_memories=10,
            provider_switching_frequency=5,  # Switch every 5 turns
        )

        run = harness.run_scenario(scenario)

        assert run.total_turns == 15
        assert run.successful_turns > 0

    def test_scenario_with_token_pressure(self):
        """Test scenario with token budget pressure."""
        mock_pipeline = MagicMock(spec=AdaptiveAssemblyPipeline)
        mock_result = AdaptiveAssemblyResult(
            query="Test query",
            provider="claude",
            compression_mode="balanced",
            compiled_context="Context",
            reasoning_context="Reasoning",
            semantic_memories="Memories",
            workspace_summary="Workspace",
            quality_score=Mock(overall_quality=Mock(return_value=0.9)),
            semantic_retention=0.88,
            token_efficiency=0.85,
            total_duration_ms=50.0,
            stage_metrics=[],
        )
        mock_pipeline.execute.return_value = mock_result

        runtime = IntegratedRuntimeSystem(mock_pipeline)
        harness = LongHorizonStressHarness(runtime)

        scenario = StressScenario(
            scenario_id="pressure-test",
            scenario_name="Token Pressure Test",
            description="Test with tight token budget",
            num_turns=10,
            num_memories=10,
            token_budget=4000,
            token_pressure_level=0.4,  # 40% of budget (tight!)
        )

        run = harness.run_scenario(scenario)

        assert run.total_turns == 10
        assert run.successful_turns > 0

    def test_get_standard_scenarios(self):
        """Test retrieving standard stress scenarios."""
        from app.runtime.stress_harness import create_standard_stress_scenarios

        scenarios = create_standard_stress_scenarios()

        assert (
            len(scenarios) == 4
        )  # baseline, recursive, provider_switching, saturation
        assert any(s.scenario_id == "baseline" for s in scenarios)
        assert any(s.scenario_id == "recursive" for s in scenarios)
        assert any(s.scenario_id == "provider_switching" for s in scenarios)
        assert any(s.scenario_id == "saturation" for s in scenarios)

    def test_baseline_scenario_properties(self):
        """Test baseline scenario has correct properties."""
        from app.runtime.stress_harness import create_standard_stress_scenarios

        scenarios = create_standard_stress_scenarios()
        baseline = next(s for s in scenarios if s.scenario_id == "baseline")

        assert baseline.num_turns == 100
        assert baseline.memory_noise_level == 0.0
        assert baseline.recursive_compression_cycles == 1
        assert baseline.token_pressure_level == 0.8

    def test_recursive_scenario_properties(self):
        """Test recursive scenario has correct properties."""
        from app.runtime.stress_harness import create_standard_stress_scenarios

        scenarios = create_standard_stress_scenarios()
        recursive = next(s for s in scenarios if s.scenario_id == "recursive")

        assert recursive.num_turns == 200
        assert recursive.recursive_compression_cycles == 4
        assert recursive.memory_growth_factor == 1.2
        assert recursive.query_complexity == "complex"

    def test_provider_switching_scenario_properties(self):
        """Test provider switching scenario has correct properties."""
        from app.runtime.stress_harness import create_standard_stress_scenarios

        scenarios = create_standard_stress_scenarios()
        switching = next(s for s in scenarios if s.scenario_id == "provider_switching")

        assert switching.provider_switching_frequency == 25
        assert switching.query_complexity == "very_complex"
        assert switching.query_diversity == 0.8

    def test_saturation_scenario_properties(self):
        """Test saturation scenario has correct properties."""
        from app.runtime.stress_harness import create_standard_stress_scenarios

        scenarios = create_standard_stress_scenarios()
        saturation = next(s for s in scenarios if s.scenario_id == "saturation")

        assert saturation.num_turns == 300
        assert saturation.num_memories == 200
        assert saturation.token_pressure_level == 0.4
        assert saturation.memory_noise_level == 0.3

    pytest.main([__file__, "-v"])
