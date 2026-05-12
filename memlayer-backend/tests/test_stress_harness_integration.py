"""
Integration tests for Phase 5B stress harness.

Tests connecting stress harness to integrated runtime and running
multi-hour simulations with realistic workloads.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta, timezone

from app.runtime import (
    IntegratedRuntimeSystem,
    LongHorizonStressHarness,
    create_standard_stress_scenarios,
    WorkspaceSimulator,
    RuntimeEvolutionTracker,
    RuntimeIntelligenceDatasetGenerator,
    EvolutionMetric,
)

from app.compiler.adaptive_assembly_pipeline import (
    AdaptiveAssemblyPipeline,
    AdaptiveAssemblyResult,
    PipelineStageMetrics,
    PipelineStage,
)


class TestStressHarnessIntegration:
    """Integration tests for stress harness with runtime."""

    def test_stress_harness_with_integrated_runtime(self):
        """Test stress harness connected to integrated runtime."""
        # Create mock pipeline
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

        # Create integrated runtime
        runtime = IntegratedRuntimeSystem(mock_pipeline)

        # Create stress harness
        harness = LongHorizonStressHarness(runtime)

        # Get standard baseline scenario
        scenarios = create_standard_stress_scenarios()
        baseline = next(s for s in scenarios if s.scenario_id == "baseline")

        # Run scenario
        run = harness.run_scenario(baseline)

        # Verify results
        assert run.total_turns == baseline.num_turns
        assert run.successful_turns > 0
        assert run.stability_score > 0

    def test_baseline_stress_scenario_full_run(self):
        """Test full baseline stress scenario."""
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
        harness = LongHorizonStressHarness(runtime)

        scenarios = create_standard_stress_scenarios()
        baseline = next(s for s in scenarios if s.scenario_id == "baseline")

        run = harness.run_scenario(baseline)

        assert run.total_turns == 100
        assert run.stability_score >= 50

    def test_recursive_stress_scenario_full_run(self):
        """Test recursive compression stress scenario."""
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
        harness = LongHorizonStressHarness(runtime)

        scenarios = create_standard_stress_scenarios()
        recursive = next(s for s in scenarios if s.scenario_id == "recursive")

        run = harness.run_scenario(recursive)

        assert run.total_turns == 200
        assert run.successful_turns > 0

    def test_provider_switching_scenario_full_run(self):
        """Test provider switching stress scenario."""
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
        harness = LongHorizonStressHarness(runtime)

        scenarios = create_standard_stress_scenarios()
        switching = next(s for s in scenarios if s.scenario_id == "provider_switching")

        run = harness.run_scenario(switching)

        assert run.total_turns == 150
        assert run.successful_turns > 0

    def test_saturation_scenario_full_run(self):
        """Test memory saturation stress scenario."""
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
        harness = LongHorizonStressHarness(runtime)

        scenarios = create_standard_stress_scenarios()
        saturation = next(s for s in scenarios if s.scenario_id == "saturation")

        run = harness.run_scenario(saturation)

        assert run.total_turns == 300
        assert run.successful_turns > 0

    def test_stress_harness_accumulates_runs(self):
        """Test that stress harness accumulates multiple runs."""
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
        harness = LongHorizonStressHarness(runtime)

        scenarios = create_standard_stress_scenarios()

        for scenario in scenarios[:2]:
            harness.run_scenario(scenario)

        assert len(harness.test_runs) == 2

    def test_stress_comparison_across_scenarios(self):
        """Test comparing stress results across scenarios."""
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
        harness = LongHorizonStressHarness(runtime)

        scenarios = create_standard_stress_scenarios()

        results = []
        for scenario in scenarios:
            run = harness.run_scenario(scenario)
            results.append(run)

        # Verify we have results for all scenarios
        assert len(results) == 4

        # All should have similar success rates (90%+)
        for result in results:
            success_rate = (
                result.successful_turns / result.total_turns
                if result.total_turns > 0
                else 0
            )
            assert success_rate >= 0.9

    def test_integration_with_evolution_tracker(self):
        """Test stress harness integration with evolution tracker."""
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
        harness = LongHorizonStressHarness(runtime)
        tracker = RuntimeEvolutionTracker()

        scenarios = create_standard_stress_scenarios()
        baseline = next(s for s in scenarios if s.scenario_id == "baseline")

        # Run scenario
        run = harness.run_scenario(baseline)

        # Record metrics in evolution tracker
        tracker.record_datapoint(
            metric=EvolutionMetric.CONTEXT_QUALITY,
            value=run.avg_quality_score,
        )
        tracker.record_datapoint(
            metric=EvolutionMetric.TOKEN_EFFICIENCY,
            value=run.avg_token_efficiency,
        )

        # Verify tracking
        summary = tracker.get_summary()
        assert summary["total_datapoints"] == 2

    def test_integration_with_workspace_simulator(self):
        """Test stress harness with workspace simulator."""
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
        harness = LongHorizonStressHarness(runtime)
        simulator = WorkspaceSimulator()

        # Create research workspace
        workspace = simulator.create_research_workspace(num_queries=30)
        ws_result = simulator.simulate_workspace(workspace)

        # Run stress scenario
        scenarios = create_standard_stress_scenarios()
        baseline = next(s for s in scenarios if s.scenario_id == "baseline")
        stress_result = harness.run_scenario(baseline)

        # Verify both worked
        assert ws_result.total_queries == 30
        assert stress_result.total_turns > 0

    def test_integration_with_dataset_generator(self):
        """Test extracting datasets from stress results."""
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
        harness = LongHorizonStressHarness(runtime)
        generator = RuntimeIntelligenceDatasetGenerator()

        # Run stress scenario
        scenarios = create_standard_stress_scenarios()
        baseline = next(s for s in scenarios if s.scenario_id == "baseline")
        stress_result = harness.run_scenario(baseline)

        # Generate dataset
        dataset = generator.generate_compression_decision_dataset(
            source="stress_test",
            num_samples=50,
        )

        # Verify dataset was created
        assert dataset.total_samples == 50
        assert dataset.source == "stress_test"

    def test_all_scenarios_telemetry_recording(self):
        """Test that all scenarios properly record telemetry."""
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
        harness = LongHorizonStressHarness(runtime)

        scenarios = create_standard_stress_scenarios()

        for scenario in scenarios:
            run = harness.run_scenario(scenario)

            # Verify telemetry was recorded
            assert run.avg_quality_score > 0
            assert run.avg_semantic_retention > 0
            assert run.stability_score > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
