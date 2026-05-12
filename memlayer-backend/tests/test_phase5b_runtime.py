"""
Tests for Phase 5B Runtime Validation Infrastructure.

Tests for integrated runtime, replay engine, and failure detection.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from app.runtime import (
    IntegratedRuntimeSystem,
    UnifiedCognitionTrace,
    RuntimeReplayEngine,
    ReplayableTrace,
    EmergentFailureDetector,
    FailureType,
    FailureSeverity,
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
            timestamp=datetime.utcnow(),
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
            timestamp=datetime.utcnow(),
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
            timestamp=datetime.utcnow(),
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
            timestamp=datetime.utcnow(),
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
            timestamp=datetime.utcnow(),
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
            timestamp=datetime.utcnow(),
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
