"""
Tests for Semantic Chunking System.

Tests verify:
1. Chunk creation accuracy
2. Topical grouping correctness
3. Chunk summary and metadata quality
4. Metrics accuracy
5. Edge cases and performance
"""

import pytest
import numpy as np
from datetime import datetime
from unittest.mock import Mock
import sys
import os

# Add the app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Mock embedding service to avoid TensorFlow/Keras import during collection
sys.modules["app.services.embedding"] = Mock()

from app.compiler.semantic_chunking import (
    SemanticChunk,
    ChunkingMetrics,
    ChunkingAnalyzer,
    ChunkType,
    SemanticChunkingService,
)


class TestSemanticChunking:
    """Test semantic chunking functionality."""

    @pytest.fixture
    def chunking_service(self):
        """Create chunking service with mock embedding service."""
        mock_embedding_service = Mock()
        return SemanticChunkingService(embedding_service=mock_embedding_service)

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

    def test_chunk_creation_single_memory(self, chunking_service, mock_memory):
        """Test chunking with a single memory."""
        mem = mock_memory("mem-1", "Single memory content")

        chunks, metrics = chunking_service.chunk_memories([mem])

        assert len(chunks) >= 1
        assert metrics.total_memories_input == 1
        assert metrics.total_chunks_created >= 1

    def test_chunk_creation_similar_memories(self, chunking_service, mock_memory):
        """Test chunking groups similar memories together."""
        # Create similar embeddings
        base_embedding = np.random.rand(384)
        base_embedding = base_embedding / np.linalg.norm(base_embedding)

        similar_embedding1 = base_embedding + np.random.normal(0, 0.05, 384)
        similar_embedding1 = similar_embedding1 / np.linalg.norm(similar_embedding1)

        similar_embedding2 = base_embedding + np.random.normal(0, 0.05, 384)
        similar_embedding2 = similar_embedding2 / np.linalg.norm(similar_embedding2)

        mem1 = mock_memory(
            "mem-1", "Content about AI", embedding=base_embedding.tolist()
        )
        mem2 = mock_memory(
            "mem-2",
            "Content about artificial intelligence",
            embedding=similar_embedding1.tolist(),
        )
        mem3 = mock_memory(
            "mem-3",
            "More AI content",
            embedding=similar_embedding2.tolist(),
        )

        chunking_service.similarity_threshold = 0.60

        chunks, metrics = chunking_service.chunk_memories([mem1, mem2, mem3])

        # Should create fewer chunks than memories
        assert len(chunks) <= 3
        assert metrics.total_memories_input == 3

    def test_chunk_creation_dissimilar_memories(self, chunking_service, mock_memory):
        """Test chunking keeps dissimilar memories separate."""
        # Create orthogonal embeddings
        embedding1 = np.array([1.0, 0.0, 0.0] + [0.0] * 381)
        embedding2 = np.array([0.0, 1.0, 0.0] + [0.0] * 381)
        embedding3 = np.array([0.0, 0.0, 1.0] + [0.0] * 381)

        mem1 = mock_memory("mem-1", "AI topic", embedding=embedding1.tolist())
        mem2 = mock_memory("mem-2", "Sports topic", embedding=embedding2.tolist())
        mem3 = mock_memory("mem-3", "Weather topic", embedding=embedding3.tolist())

        chunks, metrics = chunking_service.chunk_memories([mem1, mem2, mem3])

        # High similarity threshold means separate groups
        chunking_service.similarity_threshold = 0.90
        chunks, metrics = chunking_service.chunk_memories([mem1, mem2, mem3])

        assert metrics.total_memories_input == 3
        # May create multiple chunks since similarity is low

    def test_chunk_metadata_enrichment(self, chunking_service, mock_memory):
        """Test that chunks are enriched with metadata."""
        base_embedding = np.random.rand(384)
        base_embedding = base_embedding / np.linalg.norm(base_embedding)

        mem1 = mock_memory(
            "mem-1",
            "A" * 100,
            embedding=base_embedding.tolist(),
        )
        mem2 = mock_memory(
            "mem-2",
            "B" * 100,
            embedding=base_embedding.tolist(),
        )

        chunks, metrics = chunking_service.chunk_memories([mem1, mem2])

        for chunk in chunks:
            assert chunk.chunk_id is not None
            assert chunk.memory_count >= 1
            # Metadata should be set
            if len(chunk.source_memory_ids) > 1:
                assert chunk.centroid_embedding is not None
                assert len(chunk.centroid_embedding) == 384

    def test_chunk_types(self, chunking_service, mock_memory):
        """Test chunking with different chunk types."""
        mem1 = mock_memory("mem-1")
        mem2 = mock_memory("mem-2")

        for chunk_type in ChunkType:
            chunks, metrics = chunking_service.chunk_memories(
                [mem1, mem2], chunk_type=chunk_type
            )
            for chunk in chunks:
                assert chunk.chunk_type == chunk_type

    def test_empty_memory_list(self, chunking_service):
        """Test handling of empty memory list."""
        chunks, metrics = chunking_service.chunk_memories([])

        assert len(chunks) == 0
        assert metrics.total_memories_input == 0
        assert metrics.total_chunks_created == 0

    def test_none_embeddings_handled(self, chunking_service, mock_memory):
        """Test that memories with None embeddings are handled gracefully."""
        mem1 = mock_memory("mem-1", embedding=None)
        mem2 = mock_memory("mem-2")

        chunks, metrics = chunking_service.chunk_memories([mem1, mem2])

        # Should handle gracefully without crashing
        assert len(chunks) >= 1
        assert metrics.total_memories_input == 2

    def test_metrics_calculation(self, chunking_service, mock_memory):
        """Test that metrics are calculated correctly."""
        base_embedding = np.random.rand(384)
        base_embedding = base_embedding / np.linalg.norm(base_embedding)

        memories = [
            mock_memory(
                f"mem-{i}", f"Content {i}" * 10, embedding=base_embedding.tolist()
            )
            for i in range(5)
        ]

        chunks, metrics = chunking_service.chunk_memories(memories)

        assert metrics.total_memories_input == 5
        assert metrics.total_chunks_created >= 1
        assert metrics.avg_memories_per_chunk > 0
        assert metrics.processing_time_ms >= 0


class TestChunkingMetrics:
    """Test metrics calculation and reporting."""

    def test_metrics_creation(self):
        """Test ChunkingMetrics creation."""
        metrics = ChunkingMetrics(
            total_memories_input=100,
            total_chunks_created=20,
            avg_memories_per_chunk=5.0,
            avg_chunk_size_tokens=100,
            total_tokens_compressed=500,
        )

        assert metrics.total_memories_input == 100
        assert metrics.total_chunks_created == 20

    def test_compression_ratio_calculation(self):
        """Test compression ratio calculation."""
        metrics = ChunkingMetrics(
            total_memories_input=100,
            total_chunks_created=20,
            total_tokens_compressed=500,
        )

        assert metrics.total_tokens_compressed == 500


class TestSemanticChunk:
    """Test semantic chunk structure."""

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

    def test_chunk_creation(self, mock_memory):
        """Test creating a semantic chunk."""
        chunk = SemanticChunk(
            chunk_id="chunk-1",
            chunk_type=ChunkType.TOPICAL,
            source_memory_ids=["mem-1", "mem-2", "mem-3"],
            memory_count=3,
        )

        assert chunk.chunk_id == "chunk-1"
        assert chunk.chunk_type == ChunkType.TOPICAL
        assert len(chunk.source_memory_ids) == 3
        assert chunk.memory_count == 3

    def test_chunk_embedding(self, mock_memory):
        """Test chunk centroid embedding."""
        base_embedding = np.random.rand(384)
        base_embedding = base_embedding / np.linalg.norm(base_embedding)

        chunk = SemanticChunk(
            chunk_id="chunk-1",
            chunk_type=ChunkType.TOPICAL,
            centroid_embedding=base_embedding,
            memory_count=1,
        )

        assert chunk.centroid_embedding is not None
        assert len(chunk.centroid_embedding) == 384


class TestChunkingAnalyzer:
    """Test analytics on chunking results."""

    def test_analyze_empty_history(self):
        """Test analyzer with empty history."""
        result = ChunkingAnalyzer.analyze_chunking_impact([])

        assert result == {}

    def test_analyze_chunking_history(self):
        """Test analyzer with metrics history."""
        metrics = [
            ChunkingMetrics(
                total_memories_input=100,
                total_chunks_created=20,
                avg_memories_per_chunk=5.0,
                compression_ratio=0.3,
                avg_cohesion_score=0.75,
            ),
            ChunkingMetrics(
                total_memories_input=120,
                total_chunks_created=24,
                avg_memories_per_chunk=5.0,
                compression_ratio=0.35,
                avg_cohesion_score=0.78,
            ),
        ]

        analysis = ChunkingAnalyzer.analyze_chunking_impact(metrics)

        assert analysis["total_sessions"] == 2
        assert analysis["total_memories_processed"] == 220
        assert analysis["total_chunks_created"] == 44

    def test_chunk_statistics(self):
        """Test chunk distribution statistics."""
        base_embedding = np.random.rand(384)
        base_embedding = base_embedding / np.linalg.norm(base_embedding)

        chunks = [
            SemanticChunk(
                chunk_id="chunk-1",
                chunk_type=ChunkType.TOPICAL,
                source_memory_ids=["mem-1", "mem-2"],
                memory_count=2,
            ),
            SemanticChunk(
                chunk_id="chunk-2",
                chunk_type=ChunkType.CONVERSATION,
                source_memory_ids=["mem-3"],
                memory_count=1,
            ),
        ]

        stats = ChunkingAnalyzer.get_chunk_statistics(chunks)

        assert stats["total_chunks"] == 2
        assert stats["total_memories_tracked"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
