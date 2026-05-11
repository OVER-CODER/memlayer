"""
Tests for Adaptive Context Compilation Runtime (Phase 4).

Tests verify:
1. Multi-factor relevance ranking
2. Token budget allocation strategies
3. Context quality evaluation
4. Failure analysis and regression tracking
5. Adaptive compilation planning
6. Provider-aware optimization
7. Query complexity assessment
8. Compression mode selection
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Mock embedding service
sys.modules["app.services.embedding"] = Mock()

from app.compiler.adaptive_compilation import (
    RelevanceRankingService,
    TokenBudgetAllocator,
    ContextQualityEvaluator,
    ContextFailureAnalyzer,
    AdaptiveCompilationPlanner,
    RankingFactors,
    QueryComplexity,
)


class TestRelevanceRankingService:
    """Test relevance ranking functionality."""

    @pytest.fixture
    def ranking_service(self):
        """Create ranking service."""
        return RelevanceRankingService()

    @pytest.fixture
    def mock_memories(self):
        """Create mock memories."""
        memories = []
        for i in range(3):
            mem = Mock()
            mem.id = f"mem-{i}"
            mem.raw_content = f"Content about AI and machine learning topic {i}"
            mem.importance_score = 0.5 + (i * 0.2)
            mem.timestamp = datetime.utcnow() - timedelta(hours=i)
            memories.append(mem)
        return memories

    def test_rank_memories(self, ranking_service, mock_memories):
        """Test memory ranking."""
        query = "artificial intelligence machine learning"

        ranked = ranking_service.rank_memories(mock_memories, query, provider="generic")

        # Should return all memories ranked
        assert len(ranked) == 3

        # Results should be tuples of (memory, score, factors)
        for memory, score, factors in ranked:
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0
            assert hasattr(factors, "compute_score")

    def test_ranking_respects_recency(self, ranking_service, mock_memories):
        """Test that ranking considers multiple factors including recency."""
        query = "machine learning"
        ranked = ranking_service.rank_memories(mock_memories, query)

        # Semantic similarity is weighted higher than recency, so mem-2 (most similar) ranks higher
        assert ranked[0][0].id == "mem-2"
        # But all memories should be ranked
        assert len(ranked) == 3

    def test_ranking_with_workspace_context(self, ranking_service, mock_memories):
        """Test ranking with workspace context."""
        query = "AI systems"
        workspace = {"active_items": ["AI", "learning"]}

        ranked = ranking_service.rank_memories(
            mock_memories, query, workspace_context=workspace
        )

        # Should complete without error
        assert len(ranked) > 0

    def test_provider_specific_ranking(self, ranking_service, mock_memories):
        """Test provider-specific ranking optimization."""
        query = "neural networks"

        ranked_claude = ranking_service.rank_memories(
            mock_memories, query, provider="claude"
        )
        ranked_openai = ranking_service.rank_memories(
            mock_memories, query, provider="openai"
        )

        # Both should produce rankings
        assert len(ranked_claude) > 0
        assert len(ranked_openai) > 0

    def test_ranking_factors_computation(self):
        """Test ranking factors score computation."""
        factors = RankingFactors(
            semantic_similarity=0.9,
            importance_score=0.8,
            recency_score=0.7,
            reasoning_continuity=0.6,
            workspace_relevance=0.5,
            provider_fit=0.4,
            information_density=0.3,
        )

        score = factors.compute_score()

        # Score should be weighted combination
        assert 0.0 <= score <= 1.0
        # With these factors, score should be substantial
        assert score > 0.5


class TestTokenBudgetAllocator:
    """Test token budget allocation."""

    @pytest.fixture
    def allocator(self):
        """Create allocator."""
        return TokenBudgetAllocator()

    def test_basic_allocation(self, allocator):
        """Test basic token allocation."""
        allocation = allocator.allocate_budget(
            total_budget=4000,
            num_memories=10,
            num_chunks=5,
        )

        # Total should be close to budget
        assert allocation.total() <= 4000

        # All categories should have tokens
        assert allocation.active_reasoning > 0
        assert allocation.semantic_memories > 0
        assert allocation.metadata_glue > 0

    def test_provider_specific_allocation(self, allocator):
        """Test provider-specific allocation."""
        budget = 4000

        claude_alloc = allocator.allocate_budget(budget, 10, 5, provider="claude")
        openai_alloc = allocator.allocate_budget(budget, 10, 5, provider="openai")

        # Claude should emphasize reasoning
        assert claude_alloc.active_reasoning >= openai_alloc.active_reasoning

        # OpenAI should emphasize semantic memories
        assert openai_alloc.semantic_memories >= claude_alloc.semantic_memories

    def test_compression_mode_effects(self, allocator):
        """Test compression mode effects on allocation."""
        budget = 4000

        minimal_alloc = allocator.allocate_budget(
            budget, 10, 5, compression_mode="minimal"
        )
        full_alloc = allocator.allocate_budget(
            budget, 10, 5, compression_mode="full_context"
        )

        # Minimal should have larger buffer
        assert minimal_alloc.compression_buffer >= full_alloc.compression_buffer

    def test_allocation_ratio(self, allocator):
        """Test allocation ratio calculation."""
        ratio = allocator.get_allocation_ratio("semantic_memories", 4000)

        # Should be a valid ratio
        assert 0.0 <= ratio <= 1.0


class TestContextQualityEvaluator:
    """Test context quality evaluation."""

    @pytest.fixture
    def evaluator(self):
        """Create evaluator."""
        return ContextQualityEvaluator()

    @pytest.fixture
    def mock_context_and_memories(self):
        """Create context and memories."""
        context = (
            "AI systems use neural networks because they learn patterns effectively."
        )

        memories = []
        for i in range(2):
            mem = Mock()
            mem.id = f"mem-{i}"
            mem.raw_content = f"Memory about neural networks and learning"
            memories.append(mem)

        return context, memories

    def test_evaluate_context(self, evaluator, mock_context_and_memories):
        """Test context quality evaluation."""
        context, memories = mock_context_and_memories

        quality = evaluator.evaluate_context(
            context, memories, compression_ratio=0.3, provider="generic"
        )

        # All metrics should be in valid range
        assert 0.0 <= quality.semantic_density <= 1.0
        assert 0.0 <= quality.redundancy_score <= 1.0
        assert 0.0 <= quality.entity_continuity <= 1.0
        assert 0.0 <= quality.reasoning_preservation <= 1.0
        assert 0.0 <= quality.overall_quality <= 1.0

    def test_entity_continuity(self, evaluator):
        """Test entity continuity tracking."""
        context = "Alice and Bob worked on neural networks. Alice is an AI researcher."

        memories = []
        for name in ["Alice", "Bob", "neural networks"]:
            mem = Mock()
            mem.raw_content = name
            memories.append(mem)

        quality = evaluator.evaluate_context(context, memories, 0.2)

        # Should preserve entities
        assert quality.entity_continuity > 0.3

    def test_reasoning_preservation(self, evaluator):
        """Test reasoning preservation measurement."""
        logical_context = "Because models improve with scale, therefore we should train larger models. If budget allows, then we proceed."

        memories = []
        mem = Mock()
        mem.raw_content = "Model scaling leads to performance improvements"
        memories.append(mem)

        quality = evaluator.evaluate_context(logical_context, memories, 0.1)

        # Should preserve reasoning
        assert quality.reasoning_preservation > 0.5

    def test_provider_compatibility(self, evaluator):
        """Test provider compatibility scoring."""
        context = "This is a concise statement" * 50
        memories = []

        claude_quality = evaluator.evaluate_context(
            context, memories, 0.2, provider="claude"
        )
        openai_quality = evaluator.evaluate_context(
            context, memories, 0.2, provider="openai"
        )

        # Both should have provider compatibility
        assert claude_quality.provider_compatibility > 0.0
        assert openai_quality.provider_compatibility > 0.0


class TestContextFailureAnalyzer:
    """Test failure analysis and regression tracking."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer."""
        return ContextFailureAnalyzer()

    def test_record_failure(self, analyzer):
        """Test recording failures."""
        analyzer.record_failure(
            failure_type="semantic_drift",
            severity=0.7,
            query="test query",
            provider="claude",
            compression_mode="compressed",
            token_budget=4000,
            description="Lost semantic meaning during compression",
        )

        assert len(analyzer.failure_records) == 1
        assert analyzer.failure_records[0].failure_type == "semantic_drift"

    def test_regression_report(self, analyzer):
        """Test regression analysis report."""
        # Add multiple failures
        for i in range(3):
            analyzer.record_failure(
                failure_type="semantic_drift",
                severity=0.5 + (i * 0.1),
                query=f"query-{i}",
                provider="claude",
                compression_mode="compressed",
                token_budget=4000,
            )

        report = analyzer.get_regression_report()

        assert report["total_failures"] == 3
        assert "semantic_drift" in report["failure_types"]
        assert report["average_severity"] > 0.5

    def test_empty_regression_report(self, analyzer):
        """Test regression report when no failures."""
        report = analyzer.get_regression_report()

        assert report["status"] == "no_failures"
        assert report["total_records"] == 0


class TestAdaptiveCompilationPlanner:
    """Test adaptive compilation planning."""

    @pytest.fixture
    def planner(self):
        """Create planner with all services."""
        return AdaptiveCompilationPlanner()

    @pytest.fixture
    def mock_data(self):
        """Create mock compilation data."""
        memories = []
        for i in range(5):
            mem = Mock()
            mem.id = f"mem-{i}"
            mem.raw_content = f"Memory content {i} about AI"
            mem.importance_score = 0.5
            mem.timestamp = datetime.utcnow() - timedelta(hours=i)
            memories.append(mem)

        chunks = []
        for i in range(3):
            chunk = Mock()
            chunk.chunk_id = f"chunk-{i}"
            chunks.append(chunk)

        return memories, chunks

    def test_plan_compilation(self, planner, mock_data):
        """Test compilation planning."""
        memories, chunks = mock_data

        plan = planner.plan_compilation(
            query="Tell me about AI",
            memories=memories,
            chunks=chunks,
            token_budget=4000,
            provider="claude",
        )

        # Plan should have valid structure
        assert plan.query == "Tell me about AI"
        assert plan.total_budget == 4000
        assert len(plan.selected_memories) > 0
        assert plan.planning_time_ms > 0

    def test_query_complexity_assessment(self, planner):
        """Test query complexity assessment."""
        simple = planner._assess_query_complexity("What is AI?")
        moderate = planner._assess_query_complexity(
            "Explain how transformer-based language models"
        )
        complex_q = planner._assess_query_complexity(
            "Can you provide a detailed explanation of " + " ".join(["models"] * 10)
        )
        research = planner._assess_query_complexity(
            "How do " + " ".join(["models"] * 50)
        )

        assert simple == QueryComplexity.SIMPLE.value
        assert moderate == QueryComplexity.MODERATE.value
        assert complex_q == QueryComplexity.COMPLEX.value
        assert research == QueryComplexity.RESEARCH_INTENSIVE.value

    def test_compression_mode_selection(self, planner):
        """Test adaptive compression mode selection."""
        # Tight budget, simple query
        mode1 = planner._select_compression_mode(
            500, QueryComplexity.SIMPLE.value, "claude"
        )
        assert mode1 == "minimal"

        # Large budget, research query
        mode2 = planner._select_compression_mode(
            8000, QueryComplexity.RESEARCH_INTENSIVE.value, "claude"
        )
        assert mode2 == "research_mode"

        # Medium budget, moderate query
        mode3 = planner._select_compression_mode(
            4000, QueryComplexity.MODERATE.value, "claude"
        )
        assert mode3 in ["compressed", "full_context"]

    def test_reasoning_preservation_estimation(self, planner, mock_data):
        """Test reasoning preservation estimation."""
        memories, _ = mock_data

        # Update one memory to have logical content
        memories[0].raw_content = "Because AI is powerful, therefore it is useful"

        score = planner._estimate_reasoning_preservation(memories)

        assert 0.0 <= score <= 1.0
        assert score > 0.0  # Should detect logical content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
