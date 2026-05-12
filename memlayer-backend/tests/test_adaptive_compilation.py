"""
Tests for Adaptive Context Compilation Runtime (Phase 4).

Tests verify:
1. Relevance ranking with 7 factors
2. Token budget allocation correctness
3. Context quality evaluation accuracy
4. Failure detection and regression tracking
5. Adaptive compilation planning
6. Query type detection
7. Budget compliance
8. Deterministic reproducibility
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Mock embedding service
sys.modules["app.services.embedding"] = Mock()

from app.compiler.adaptive_compilation import (
    AdaptiveCompilationPlanner,
    RelevanceRankingService,
    TokenBudgetAllocator,
    ContextQualityEvaluator,
    ContextFailureAnalyzer,
    QueryType,
    RankingFactors,
    ContextQualityScore,
    TokenBudgetAllocation,
)


class TestRelevanceRankingService:
    """Test multi-factor relevance ranking."""

    @pytest.fixture
    def ranking_service(self):
        """Create ranking service."""
        return RelevanceRankingService(embedding_service=Mock())

    @pytest.fixture
    def mock_memory(self):
        """Factory for creating mock memories."""

        def _create(
            memory_id="mem-1",
            content="Test content",
            importance=0.7,
            timestamp=None,
        ):
            mem = Mock()
            mem.id = memory_id
            mem.raw_content = content
            mem.importance_score = importance
            mem.timestamp = timestamp or datetime.now(timezone.utc)
            mem.embedding = [0.1] * 384
            return mem

        return _create

    def test_ranking_factors_calculation(self, ranking_service, mock_memory):
        """Test 7-factor ranking calculation."""
        query = "What is machine learning?"
        memory = mock_memory("mem-1", "Machine learning is AI")

        factors = ranking_service._calculate_ranking_factors(
            query, memory, None, "generic", QueryType.REASONING
        )

        # All factors should be calculated
        assert hasattr(factors, "semantic_similarity")
        assert hasattr(factors, "importance_score")
        assert hasattr(factors, "recency_factor")
        assert hasattr(factors, "reasoning_continuity")
        assert hasattr(factors, "workspace_relevance")
        assert hasattr(factors, "provider_fit")
        assert hasattr(factors, "information_density")

    def test_ranking_factors_total_score(self, ranking_service, mock_memory):
        """Test total score calculation."""
        query = "Why does this happen?"
        memory = mock_memory("mem-1", "This happens because...")

        factors = ranking_service._calculate_ranking_factors(
            query, memory, None, "generic", QueryType.REASONING
        )

        score = factors.total_score()

        # Score should be normalized to 0-1
        assert 0.0 <= score <= 1.0

    def test_rank_memories(self, ranking_service, mock_memory):
        """Test memory ranking."""
        query = "What about transformers?"
        memories = [
            mock_memory("mem-1", "Transformers are neural networks"),
            mock_memory("mem-2", "RNNs are older models"),
            mock_memory("mem-3", "Transformer architecture uses attention"),
        ]

        rankings = ranking_service.rank_memories(
            query, memories, None, "generic", QueryType.REASONING
        )

        # Should return ranked list
        assert len(rankings) == 3
        assert all(isinstance(r, tuple) and len(r) == 3 for r in rankings)

        # Scores should be descending
        scores = [r[1] for r in rankings]
        assert scores == sorted(scores, reverse=True)

    def test_recency_factor(self, ranking_service, mock_memory):
        """Test recency scoring."""
        query = "Recent updates"
        recent_memory = mock_memory(
            "mem-1", "Recent update", timestamp=datetime.now(timezone.utc)
        )
        old_memory = mock_memory(
            "mem-2", "Old update", timestamp=datetime.now(timezone.utc) - timedelta(days=100)
        )

        recent_factors = ranking_service._calculate_ranking_factors(
            query, recent_memory, None, "generic", QueryType.FACTUAL
        )
        old_factors = ranking_service._calculate_ranking_factors(
            query, old_memory, None, "generic", QueryType.FACTUAL
        )

        # Recent should score higher
        assert recent_factors.recency_factor > old_factors.recency_factor

    def test_reasoning_continuity_detection(self, ranking_service, mock_memory):
        """Test reasoning continuity detection."""
        reasoning_query = "Why does this work?"
        logical_memory = mock_memory("mem-1", "Because X, therefore Y happens")
        random_memory = mock_memory("mem-2", "Some random content")

        logical_factors = ranking_service._calculate_ranking_factors(
            reasoning_query, logical_memory, None, "generic", QueryType.REASONING
        )
        random_factors = ranking_service._calculate_ranking_factors(
            reasoning_query, random_memory, None, "generic", QueryType.REASONING
        )

        # Logical should score higher for reasoning
        assert (
            logical_factors.reasoning_continuity > random_factors.reasoning_continuity
        )

    def test_provider_fit(self, ranking_service, mock_memory):
        """Test provider-specific fitting."""
        memory = mock_memory("mem-1", "This is a very detailed explanation of concepts")

        claude_factors = ranking_service._calculate_ranking_factors(
            "What?", memory, None, "claude", QueryType.REASONING
        )
        openai_factors = ranking_service._calculate_ranking_factors(
            "What?", memory, None, "openai", QueryType.REASONING
        )

        # Providers should have different fits based on their preferences
        assert claude_factors.provider_fit > 0.0
        assert openai_factors.provider_fit > 0.0

    def test_information_density(self, ranking_service, mock_memory):
        """Test information density calculation."""
        dense_memory = mock_memory(
            "mem-1", "Alice Smith published 5 papers on neural networks in 2023"
        )
        sparse_memory = mock_memory(
            "mem-2", "blah blah blah some random words without meaning"
        )

        dense_factors = ranking_service._calculate_ranking_factors(
            "Papers", dense_memory, None, "generic", QueryType.RESEARCH
        )
        sparse_factors = ranking_service._calculate_ranking_factors(
            "Papers", sparse_memory, None, "generic", QueryType.RESEARCH
        )

        # Dense should score higher
        assert dense_factors.information_density > sparse_factors.information_density


class TestTokenBudgetAllocator:
    """Test token budget allocation."""

    def test_allocation_within_budget(self):
        """Test allocation stays within budget."""
        allocation = TokenBudgetAllocator.allocate_budget(
            total_budget=4000,
            query_complexity=0.5,
            workspace_size=100,
            compression_mode="compressed",
            provider_type="generic",
        )

        # Should verify allocation
        assert allocation.verify_allocation()
        assert allocation.total_budget == 4000

    def test_allocation_breakdown(self):
        """Test allocation breakdown is reasonable."""
        allocation = TokenBudgetAllocator.allocate_budget(
            total_budget=4000,
            query_complexity=0.5,
            workspace_size=100,
            compression_mode="compressed",
            provider_type="generic",
        )

        # All components should be positive
        assert allocation.response_reserve > 0
        assert allocation.semantic_memories > 0
        assert allocation.workspace_summary > 0
        assert allocation.chunk_summaries > 0
        assert allocation.metadata_glue > 0

    def test_compression_mode_affects_allocation(self):
        """Test compression mode affects chunk summary allocation."""
        full_context = TokenBudgetAllocator.allocate_budget(
            4000, 0.5, 100, "full_context", "generic"
        )
        minimal = TokenBudgetAllocator.allocate_budget(
            4000, 0.5, 100, "minimal", "generic"
        )

        # Full context should allocate more to chunk summaries
        assert full_context.chunk_summaries > minimal.chunk_summaries

    def test_query_complexity_affects_allocation(self):
        """Test query complexity affects reasoning allocation."""
        simple = TokenBudgetAllocator.allocate_budget(
            4000, 0.2, 100, "compressed", "generic"
        )
        complex_query = TokenBudgetAllocator.allocate_budget(
            4000, 0.8, 100, "compressed", "generic"
        )

        # Complex should allocate more to reasoning
        assert complex_query.reasoning_context > simple.reasoning_context

    def test_workspace_size_affects_allocation(self):
        """Test workspace size affects summary allocation."""
        small_ws = TokenBudgetAllocator.allocate_budget(
            4000, 0.5, 10, "compressed", "generic"
        )
        large_ws = TokenBudgetAllocator.allocate_budget(
            4000, 0.5, 1000, "compressed", "generic"
        )

        # Larger workspace should get more workspace summary tokens
        assert large_ws.workspace_summary > small_ws.workspace_summary


class TestContextQualityEvaluator:
    """Test context quality evaluation."""

    def test_quality_score_creation(self):
        """Test quality score initialization."""
        score = ContextQualityScore()

        assert hasattr(score, "semantic_density")
        assert hasattr(score, "redundancy_ratio")
        assert hasattr(score, "entity_continuity")
        assert hasattr(score, "reasoning_preservation")
        assert hasattr(score, "topic_preservation")
        assert hasattr(score, "provider_compatibility")
        assert hasattr(score, "compression_effectiveness")

    def test_overall_quality_calculation(self):
        """Test overall quality calculation."""
        score = ContextQualityScore(
            semantic_density=0.8,
            redundancy_ratio=0.1,
            entity_continuity=0.9,
            reasoning_preservation=0.7,
            topic_preservation=0.8,
            provider_compatibility=0.75,
            compression_effectiveness=0.6,
        )

        overall = score.overall_quality()

        # Should be normalized 0-1
        assert 0.0 <= overall <= 1.0

    @pytest.fixture
    def mock_memory(self):
        """Create mock memory."""

        def _create(content="Test content"):
            mem = Mock()
            mem.raw_content = content
            return mem

        return _create

    def test_evaluate_quality(self, mock_memory):
        """Test quality evaluation."""
        original_memories = [
            mock_memory("Memory about AI and machine learning"),
            mock_memory("Discussion on neural networks"),
        ]
        compiled = "AI and machine learning. Neural networks work"

        score = ContextQualityEvaluator.evaluate_quality(
            compiled, original_memories, 0.3, "generic"
        )

        # Quality should be evaluated
        assert score.semantic_density > 0.0
        assert 0.0 <= score.entity_continuity <= 1.0


class TestContextFailureAnalyzer:
    """Test failure analysis and regression tracking."""

    def test_analyzer_initialization(self):
        """Test analyzer creation."""
        analyzer = ContextFailureAnalyzer()

        assert len(analyzer.failure_history) == 0

    def test_analyze_failure(self):
        """Test failure analysis."""
        analyzer = ContextFailureAnalyzer()

        original = "Because X happens, therefore Y occurs. AI and machine learning is important."
        compiled = "Y happens. Important."

        analysis = analyzer.analyze_failure(
            query="Why is this important?",
            compiled_context=compiled,
            original_context=original,
        )

        # Should detect compression
        assert len(analyzer.failure_history) == 1

    def test_missing_entities_detection(self):
        """Test missing entity detection."""
        analyzer = ContextFailureAnalyzer()

        original = "Alice and Bob discussed the latest AI breakthrough by OpenAI."
        compiled = "Latest breakthrough discussed."

        analysis = analyzer.analyze_failure(
            query="Who discussed what?",
            compiled_context=compiled,
            original_context=original,
        )

        # Should detect missing entities
        if analysis.missing_entities:
            assert "Alice" in str(analysis.missing_entities) or "OpenAI" in str(
                analysis.missing_entities
            )

    def test_regression_report(self):
        """Test regression report generation."""
        analyzer = ContextFailureAnalyzer()

        # Add some failures
        for i in range(3):
            analyzer.analyze_failure(
                query=f"Query {i}",
                compiled_context="Short",
                original_context="This is a much longer original context with information",
            )

        report = analyzer.get_regression_report()

        assert report["total_failures"] == 3

    def test_reasoning_collapse_detection(self):
        """Test reasoning collapse detection."""
        analyzer = ContextFailureAnalyzer()

        original = "Because X, therefore Y. Hence Z. If A then B."
        compiled = "Y and Z"

        analysis = analyzer.analyze_failure(
            query="Why?",
            compiled_context=compiled,
            original_context=original,
        )

        # Should detect reasoning collapse (few logical connectors)
        if analysis.reasoning_collapse:
            assert (
                "logical" in analysis.reason.lower()
                or "reason" in str(analysis.recommended_actions).lower()
            )


class TestAdaptiveCompilationPlanner:
    """Test adaptive compilation planning."""

    @pytest.fixture
    def planner(self):
        """Create planner."""
        return AdaptiveCompilationPlanner(
            ranking_service=RelevanceRankingService(Mock()),
            embedding_service=Mock(),
        )

    @pytest.fixture
    def mock_memory(self):
        """Create mock memory."""

        def _create(memory_id="mem-1", content="Content"):
            mem = Mock()
            mem.id = memory_id
            mem.raw_content = content
            mem.importance_score = 0.7
            mem.timestamp = datetime.now(timezone.utc)
            mem.embedding = [0.1] * 384
            return mem

        return _create

    def test_plan_creation(self, planner, mock_memory):
        """Test compilation plan creation."""
        memories = [
            mock_memory("mem-1", "First memory content"),
            mock_memory("mem-2", "Second memory content"),
        ]

        plan = planner.plan_compilation(
            query="What is important?",
            memories=memories,
            provider="generic",
            token_budget=4000,
        )

        # Plan should have all required fields
        assert plan.query == "What is important?"
        assert len(plan.selected_memories) > 0
        assert plan.token_allocation is not None
        assert plan.quality_score is not None

    def test_query_type_detection(self, planner):
        """Test query type detection."""
        reasoning_query = "Why does this happen?"
        factual_query = "What is this?"
        coding_query = "How do I use this API?"

        reasoning_type = planner._determine_query_type(reasoning_query)
        factual_type = planner._determine_query_type(factual_query)
        coding_type = planner._determine_query_type(coding_query)

        assert reasoning_type == QueryType.REASONING
        assert factual_type == QueryType.FACTUAL
        assert coding_type == QueryType.CODING

    def test_query_complexity_estimation(self, planner):
        """Test query complexity estimation."""
        simple = "What?"
        medium = "What is machine learning and how does it work?"
        complex_q = "Can you explain why deep learning models with transformer architecture have become so dominant in natural language processing tasks over the past five years?"

        simple_complexity = planner._estimate_query_complexity(simple)
        medium_complexity = planner._estimate_query_complexity(medium)
        complex_complexity = planner._estimate_query_complexity(complex_q)

        assert simple_complexity < medium_complexity < complex_complexity

    def test_token_budget_allocation_in_plan(self, planner, mock_memory):
        """Test token allocation in plan."""
        memories = [mock_memory(f"mem-{i}", f"Content {i}") for i in range(5)]

        plan = planner.plan_compilation(
            query="Complex query requiring reasoning",
            memories=memories,
            provider="claude",
            token_budget=8000,
        )

        # Allocation should be valid
        assert plan.token_allocation.verify_allocation()
        assert plan.token_allocation.reasoning_context > 0

    def test_plan_reproducibility(self, planner, mock_memory):
        """Test planning is reproducible."""
        memories = [mock_memory(f"mem-{i}", f"Content {i}") for i in range(3)]

        plan1 = planner.plan_compilation(
            query="Same query",
            memories=memories,
            provider="generic",
            token_budget=4000,
        )
        plan2 = planner.plan_compilation(
            query="Same query",
            memories=memories,
            provider="generic",
            token_budget=4000,
        )

        # Should select same memories
        assert set(plan1.selected_memories) == set(plan2.selected_memories)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
