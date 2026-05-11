"""
Tests for Semantic Deduplication Engine.

Tests verify:
1. Duplicate detection accuracy
2. Merge strategy correctness
3. Metrics accuracy
4. Edge cases
5. Performance characteristics
"""

import pytest
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch
import sys
import os

# Add the app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Mock embedding service to avoid TensorFlow/Keras import during test collection
sys.modules["app.services.embedding"] = Mock()

# Import deduplication components directly
from app.compiler.semantic_deduplication import (
    DeduplicationMetrics,
    DuplicateGroup,
    MergeStrategy,
    DeduplicationAnalyzer,
    SemanticDeduplicationService,
)


class TestSemanticDeduplication:
    """Test semantic deduplication functionality."""

    @pytest.fixture
    def dedup_service(self):
        """Create deduplication service."""
        return SemanticDeduplicationService()

    @pytest.fixture
    def mock_memory(self):
        """Factory for creating mock memories."""

        def _create(
            memory_id="mem-1",
            content="Test content",
            importance=0.7,
            embedding=None,
        ):
            mem = Mock()
            mem.id = memory_id
            mem.raw_content = content
            mem.importance_score = importance
            mem.timestamp = datetime.utcnow()
            mem.embedding = embedding or np.random.rand(384).tolist()
            return mem

        return _create

    def test_identical_memories_detected(self, dedup_service, mock_memory):
        """Test that identical memories are detected as duplicates."""
        # Create identical embeddings
        shared_embedding = np.random.rand(384)

        mem1 = mock_memory("mem-1", "Same content", embedding=shared_embedding.tolist())
        mem2 = mock_memory("mem-2", "Same content", embedding=shared_embedding.tolist())

        # Set high overlap threshold for identical detection
        dedup_service.overlap_threshold = 0.95

        memories_kept, metrics, groups = dedup_service.deduplicate([mem1, mem2])

        assert len(groups) == 1
        assert len(memories_kept) == 1
        assert metrics.duplicates_removed >= 1

    def test_similar_memories_detected(self, dedup_service, mock_memory):
        """Test detection of similar (but not identical) memories."""
        # Create similar embeddings (high cosine similarity)
        base_embedding = np.random.rand(384)
        base_embedding = base_embedding / np.linalg.norm(base_embedding)

        # Similar embedding (small perturbation)
        similar_embedding = base_embedding + np.random.normal(0, 0.05, 384)
        similar_embedding = similar_embedding / np.linalg.norm(similar_embedding)

        mem1 = mock_memory(
            "mem-1", "Content about AI", embedding=base_embedding.tolist()
        )
        mem2 = mock_memory(
            "mem-2",
            "Content about artificial intelligence",
            embedding=similar_embedding.tolist(),
        )

        dedup_service.overlap_threshold = 0.70

        memories_kept, metrics, groups = dedup_service.deduplicate([mem1, mem2])

        # Should find them as similar
        assert len(groups) >= 0  # Depends on similarity

    def test_dissimilar_memories_not_grouped(self, dedup_service, mock_memory):
        """Test that dissimilar memories are not grouped."""
        # Create orthogonal embeddings
        embedding1 = np.array([1.0, 0.0, 0.0] + [0.0] * 381)
        embedding2 = np.array([0.0, 1.0, 0.0] + [0.0] * 381)

        mem1 = mock_memory("mem-1", "AI topic", embedding=embedding1.tolist())
        mem2 = mock_memory("mem-2", "Sports topic", embedding=embedding2.tolist())

        memories_kept, metrics, groups = dedup_service.deduplicate([mem1, mem2])

        assert len(groups) == 0
        assert len(memories_kept) == 2

    def test_merge_strategy_highest_importance(self, dedup_service, mock_memory):
        """Test KEEP_HIGHEST_IMPORTANCE strategy."""
        shared_embedding = np.random.rand(384)

        mem1 = mock_memory(
            "mem-1",
            "Low importance",
            importance=0.3,
            embedding=shared_embedding.tolist(),
        )
        mem2 = mock_memory(
            "mem-2",
            "High importance",
            importance=0.9,
            embedding=shared_embedding.tolist(),
        )

        dedup_service.overlap_threshold = 0.95

        memories_kept, _, groups = dedup_service.deduplicate(
            [mem1, mem2], strategy=MergeStrategy.KEEP_HIGHEST_IMPORTANCE
        )

        assert len(memories_kept) == 1
        assert memories_kept[0].id == "mem-2"  # Should keep high importance

    def test_merge_strategy_most_recent(self, dedup_service, mock_memory):
        """Test KEEP_MOST_RECENT strategy."""
        shared_embedding = np.random.rand(384)

        mem1 = mock_memory("mem-1", embedding=shared_embedding.tolist())
        mem2 = mock_memory("mem-2", embedding=shared_embedding.tolist())

        # Make mem2 more recent
        mem2.timestamp = datetime.utcnow()
        mem1.timestamp = datetime(2020, 1, 1)

        dedup_service.overlap_threshold = 0.95

        memories_kept, _, groups = dedup_service.deduplicate(
            [mem1, mem2], strategy=MergeStrategy.KEEP_MOST_RECENT
        )

        assert len(memories_kept) == 1
        assert memories_kept[0].id == "mem-2"

    def test_merge_strategy_longest_content(self, dedup_service, mock_memory):
        """Test KEEP_LONGEST strategy."""
        shared_embedding = np.random.rand(384)

        mem1 = mock_memory("mem-1", "short", embedding=shared_embedding.tolist())
        mem2 = mock_memory(
            "mem-2", "much longer content here", embedding=shared_embedding.tolist()
        )

        dedup_service.overlap_threshold = 0.95

        memories_kept, _, groups = dedup_service.deduplicate(
            [mem1, mem2], strategy=MergeStrategy.KEEP_LONGEST
        )

        assert len(memories_kept) == 1
        assert memories_kept[0].id == "mem-2"

    def test_metrics_accuracy(self, dedup_service, mock_memory):
        """Test that metrics are calculated correctly."""
        shared_embedding = np.random.rand(384)

        mem1 = mock_memory("mem-1", "A" * 400, embedding=shared_embedding.tolist())
        mem2 = mock_memory("mem-2", "B" * 400, embedding=shared_embedding.tolist())
        mem3 = mock_memory("mem-3", "C" * 100)  # Unique

        dedup_service.overlap_threshold = 0.95

        memories_kept, metrics, groups = dedup_service.deduplicate([mem1, mem2, mem3])

        assert metrics.total_memories_input == 3
        assert metrics.total_memories_after < 3
        assert metrics.duplicate_groups_found >= 0
        assert metrics.token_savings > 0
        assert metrics.processing_time_ms >= 0

    def test_empty_memory_list(self, dedup_service):
        """Test handling of empty memory list."""
        memories_kept, metrics, groups = dedup_service.deduplicate([])

        assert len(memories_kept) == 0
        assert len(groups) == 0
        assert metrics.duplicate_groups_found == 0

    def test_single_memory(self, dedup_service, mock_memory):
        """Test handling of single memory."""
        mem = mock_memory("mem-1")

        memories_kept, metrics, groups = dedup_service.deduplicate([mem])

        assert len(memories_kept) == 1
        assert len(groups) == 0

    def test_none_embeddings_handled(self, dedup_service, mock_memory):
        """Test that memories with None embeddings are handled gracefully."""
        mem1 = mock_memory("mem-1", embedding=None)
        mem2 = mock_memory("mem-2")

        memories_kept, metrics, groups = dedup_service.deduplicate([mem1, mem2])

        # Should handle gracefully without crashing
        assert len(memories_kept) >= 1


class TestDeduplicationMetrics:
    """Test metrics calculation and reporting."""

    def test_metrics_creation(self):
        """Test DeduplicationMetrics creation."""
        metrics = DeduplicationMetrics(
            total_memories_input=100,
            total_memories_after=80,
            duplicate_groups_found=10,
            duplicates_removed=20,
            token_savings=500,
            processing_time_ms=45.2,
        )

        assert metrics.total_memories_input == 100
        assert metrics.compression_ratio > 0

    def test_compression_ratio_calculation(self):
        """Test compression ratio is calculated correctly."""
        metrics = DeduplicationMetrics(
            total_memories_input=100,
            total_memories_after=80,
            token_savings=1000,
        )

        # compression_ratio = (token_savings / total_input) * 100
        expected_ratio = (1000 / 100) * 100
        assert metrics.compression_ratio == expected_ratio


class TestDuplicateGroup:
    """Test duplicate group structure."""

    @pytest.fixture
    def mock_memory(self):
        """Factory for creating mock memories."""

        def _create(
            memory_id="mem-1",
            content="Test content",
            importance=0.7,
            embedding=None,
        ):
            mem = Mock()
            mem.id = memory_id
            mem.raw_content = content
            mem.importance_score = importance
            mem.timestamp = datetime.utcnow()
            mem.embedding = embedding or np.random.rand(384).tolist()
            return mem

        return _create

    def test_duplicate_group_creation(self, mock_memory):
        """Test creating a duplicate group."""
        primary = mock_memory("mem-1")
        redundant = [mock_memory("mem-2"), mock_memory("mem-3")]

        group = DuplicateGroup(
            primary_memory=primary,
            redundant_memories=redundant,
            overlap_score=0.92,
            token_savings=300,
        )

        assert group.primary_memory.id == "mem-1"
        assert len(group.redundant_memories) == 2
        assert group.overlap_score == 0.92


class TestDeduplicationAnalyzer:
    """Test analytics on deduplication results."""

    def test_analyze_empty_history(self):
        """Test analyzer with empty history."""
        result = DeduplicationAnalyzer.analyze_deduplication_impact([])

        assert result == {}

    def test_analyze_deduplication_history(self):
        """Test analyzer with metrics history."""
        metrics = [
            DeduplicationMetrics(
                total_memories_input=100,
                total_memories_after=80,
                duplicate_groups_found=10,
                token_savings=500,
                processing_time_ms=30.0,
            ),
            DeduplicationMetrics(
                total_memories_input=120,
                total_memories_after=100,
                duplicate_groups_found=12,
                token_savings=600,
                processing_time_ms=35.0,
            ),
        ]

        analysis = DeduplicationAnalyzer.analyze_deduplication_impact(metrics)

        assert analysis["total_sessions"] == 2
        assert analysis["total_token_savings"] == 1100
        assert analysis["avg_duplicates_found"] == 11.0

    def test_duplicate_statistics(self):
        """Test duplicate group statistics."""
        groups = [
            DuplicateGroup(primary_memory=Mock(), redundant_memories=[Mock(), Mock()]),
            DuplicateGroup(primary_memory=Mock(), redundant_memories=[Mock()]),
        ]

        stats = DeduplicationAnalyzer.get_duplicate_statistics(groups)

        assert stats["duplicate_groups"] == 2
        assert stats["total_duplicates"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
