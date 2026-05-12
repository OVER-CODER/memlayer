"""
Tests for Adaptive Assembly Pipeline.

Tests the end-to-end context compilation pipeline integrating all Phase 4 components.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
import numpy as np

from app.compiler.adaptive_assembly_pipeline import (
    AdaptiveAssemblyPipeline,
    PipelineStage,
    AdaptiveAssemblyResult,
)
from app.compiler.adaptive_compilation import (
    RelevanceRankingService,
)


@pytest.fixture
def mock_memory():
    """Create mock memory."""

    def _create_mock_memory(mem_id, content, importance=0.5, timestamp=None):
        mem = Mock()
        mem.id = mem_id
        mem.raw_content = content
        mem.importance_score = importance
        mem.timestamp = timestamp or datetime.now(timezone.utc)
        mem.embedding = np.random.random(768).tolist()
        return mem

    return _create_mock_memory


@pytest.fixture
def pipeline(mock_memory):
    """Create adaptive assembly pipeline."""
    ranking_service = RelevanceRankingService(Mock())
    return AdaptiveAssemblyPipeline(
        ranking_service=ranking_service,
        embedding_service=Mock(),
        compression_mode="balanced",
    )


class TestAdaptiveAssemblyPipeline:
    """Test adaptive assembly pipeline."""

    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initialization."""
        assert pipeline is not None
        assert pipeline.ranking_service is not None
        assert pipeline.compression_mode == "balanced"
        assert len(pipeline.execution_history) == 0

    def test_pipeline_execution(self, pipeline, mock_memory):
        """Test complete pipeline execution."""
        memories = [
            mock_memory("mem-1", "Machine learning is a subset of AI"),
            mock_memory("mem-2", "Deep learning uses neural networks"),
            mock_memory("mem-3", "Transformers revolutionized NLP"),
        ]

        result = pipeline.execute(
            query="What is machine learning?",
            memories=memories,
            original_context="Original context here",
            token_budget=4000,
            provider="claude",
        )

        assert result is not None
        assert result.query == "What is machine learning?"
        assert result.provider == "claude"
        assert result.compiled_context  # Should have content
        assert result.total_duration_ms > 0
        assert len(result.stage_metrics) > 0

    def test_pipeline_stage_metrics(self, pipeline, mock_memory):
        """Test pipeline stage metrics tracking."""
        memories = [mock_memory(f"mem-{i}", f"Content {i}") for i in range(5)]

        result = pipeline.execute(
            query="Test query",
            memories=memories,
            token_budget=4000,
            provider="claude",
        )

        # Verify stage metrics
        assert len(result.stage_metrics) > 0

        # Find specific stages
        stages_found = {m.stage for m in result.stage_metrics}
        assert PipelineStage.RANKING in stages_found
        assert PipelineStage.ALLOCATION in stages_found
        assert PipelineStage.ASSEMBLY in stages_found

    def test_pipeline_quality_score(self, pipeline, mock_memory):
        """Test quality scoring in pipeline."""
        memories = [
            mock_memory("mem-1", "Important information 1"),
            mock_memory("mem-2", "Important information 2"),
        ]

        result = pipeline.execute(
            query="What is important?",
            memories=memories,
            original_context="Original information",
            token_budget=4000,
            provider="claude",
        )

        assert result.quality_score is not None
        assert 0.0 <= result.quality_score.overall_quality() <= 1.0
        assert result.semantic_retention >= 0.0

    def test_pipeline_execution_history(self, pipeline, mock_memory):
        """Test execution history tracking."""
        memories = [mock_memory(f"mem-{i}", f"Content {i}") for i in range(3)]

        # Run pipeline multiple times
        for i in range(3):
            pipeline.execute(
                query=f"Query {i}",
                memories=memories,
                token_budget=4000,
                provider="claude",
            )

        assert len(pipeline.execution_history) == 3

    def test_pipeline_analytics_report(self, pipeline, mock_memory):
        """Test analytics report generation."""
        memories = [mock_memory(f"mem-{i}", f"Content {i}") for i in range(5)]

        # Run pipeline
        pipeline.execute(
            query="Test query",
            memories=memories,
            token_budget=4000,
            provider="claude",
        )

        report = pipeline.get_analytics_report()

        assert report["total_executions"] == 1
        assert "avg_total_time_ms" in report
        assert "avg_quality_score" in report
        assert report["avg_total_time_ms"] > 0

    def test_pipeline_different_providers(self, pipeline, mock_memory):
        """Test pipeline with different providers."""
        memories = [mock_memory(f"mem-{i}", f"Content {i}") for i in range(5)]

        providers = ["claude", "openai", "gemini"]
        results = []

        for provider in providers:
            result = pipeline.execute(
                query="Test query",
                memories=memories,
                token_budget=4000,
                provider=provider,
            )
            results.append(result)

        # All should complete without error
        assert len(results) == 3
        for result in results:
            assert result.provider in providers

    def test_pipeline_token_budget_impact(self, pipeline, mock_memory):
        """Test impact of different token budgets."""
        memories = [mock_memory(f"mem-{i}", f"Content {i}") for i in range(10)]

        budgets = [2000, 4000, 8000]
        results = []

        for budget in budgets:
            result = pipeline.execute(
                query="Test query",
                memories=memories,
                token_budget=budget,
                provider="claude",
            )
            results.append(result)

        # Higher budgets should generally allow more tokens
        assert len(results) == 3
        for result in results:
            assert result.token_efficiency >= 0

    def test_pipeline_error_handling(self, pipeline, mock_memory):
        """Test error handling in pipeline."""
        # Simulate error by providing empty memories
        result = pipeline.execute(
            query="Test query",
            memories=[],
            token_budget=4000,
            provider="claude",
        )

        # Should return a result even with empty memories
        assert result is not None
        assert result.query == "Test query"
        # Should have some stage metrics despite handling

    def test_pipeline_compilation_plan_in_result(self, pipeline, mock_memory):
        """Test that compilation plan is included in result."""
        memories = [mock_memory(f"mem-{i}", f"Content {i}") for i in range(5)]

        result = pipeline.execute(
            query="Test query",
            memories=memories,
            token_budget=4000,
            provider="claude",
        )

        assert result.compilation_plan is not None
        assert len(result.compilation_plan.selected_memories) > 0

    def test_pipeline_workspace_state(self, pipeline, mock_memory):
        """Test pipeline with workspace state."""
        memories = [mock_memory(f"mem-{i}", f"Content {i}") for i in range(5)]

        workspace_state = {
            "current_focus": "machine learning",
            "recent_queries": ["What is ML?", "How does it work?"],
        }

        result = pipeline.execute(
            query="Tell me more",
            memories=memories,
            token_budget=4000,
            provider="claude",
            workspace_state=workspace_state,
        )

        assert result is not None
        assert result.compiled_context


class TestPipelineStageMetrics:
    """Test pipeline stage metrics."""

    def test_stage_metrics_creation(self):
        """Test stage metrics creation."""
        from app.compiler.adaptive_assembly_pipeline import PipelineStageMetrics

        metric = PipelineStageMetrics(
            stage=PipelineStage.RANKING,
            duration_ms=1.23,
            input_count=10,
            output_count=8,
            memory_delta_bytes=1024,
            notes="Test note",
        )

        assert metric.stage == PipelineStage.RANKING
        assert metric.duration_ms == 1.23
        assert metric.input_count == 10
        assert metric.output_count == 8
        assert metric.memory_delta_bytes == 1024
        assert metric.notes == "Test note"


class TestAdaptiveAssemblyResult:
    """Test assembly result."""

    def test_result_to_dict(self):
        """Test result conversion to dict."""
        result = AdaptiveAssemblyResult(
            query="Test query",
            provider="claude",
            compression_mode="balanced",
            compiled_context="Test context",
            reasoning_context="Reasoning here",
            semantic_memories="Memories here",
            workspace_summary="Summary here",
            semantic_retention=0.85,
            token_efficiency=0.75,
            total_duration_ms=10.5,
        )

        result_dict = result.to_dict()

        assert result_dict["query"] == "Test query"
        assert result_dict["provider"] == "claude"
        assert result_dict["compression_mode"] == "balanced"
        assert "timestamp" in result_dict
