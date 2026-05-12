"""
Benchmark suite for Semantic Chunking System.

Measures:
- Chunking performance and latency
- Chunk quality metrics (cohesion, compression)
- Scalability with memory count
- Effectiveness against LOCOMO-style workloads
"""

import time
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
import json
from datetime import datetime, timezone
from unittest.mock import Mock
import sys
import os

# Mock embedding service to avoid TensorFlow/Keras import during collection
sys.modules["app.services.embedding"] = Mock()

from app.compiler.semantic_chunking import (
    SemanticChunkingService,
    ChunkingMetrics,
    ChunkType,
)
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChunkingBenchmarkResult:
    """Result of a single chunking benchmark run."""

    benchmark_name: str
    timestamp: datetime
    num_memories: int
    chunk_type: str

    # Performance
    processing_time_ms: float
    chunks_created: int
    avg_memories_per_chunk: float

    # Quality
    compression_ratio: float
    avg_cohesion_score: float
    chunk_fragmentation: float

    def to_dict(self):
        return asdict(self)


class ChunkingBenchmark:
    """Benchmark suite for chunking engine."""

    def __init__(self):
        # Create service with mock embedding service to avoid TensorFlow imports
        mock_embedding_service = Mock()
        self.service = SemanticChunkingService(embedding_service=mock_embedding_service)
        self.results: List[ChunkingBenchmarkResult] = []

    def run_all_benchmarks(self) -> Dict:
        """Run complete benchmark suite."""
        logger.info("Starting chunking benchmarks...")

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "benchmarks": {
                "small_dataset": self.benchmark_small_dataset(),
                "medium_dataset": self.benchmark_medium_dataset(),
                "large_dataset": self.benchmark_large_dataset(),
                "chunk_type_comparison": self.benchmark_chunk_type_comparison(),
            },
        }

        return results

    def _create_memory(
        self,
        memory_id: str,
        content: str,
        importance: float = 0.7,
        embedding: np.ndarray = None,
    ):
        """Create mock memory object."""
        mem = Mock()
        mem.id = memory_id
        mem.raw_content = content
        mem.importance_score = importance
        mem.timestamp = datetime.now(timezone.utc)
        if embedding is None:
            mem.embedding = (
                np.random.rand(384) / np.linalg.norm(np.random.rand(384))
            ).tolist()
        else:
            mem.embedding = embedding.tolist()
        return mem

    def benchmark_small_dataset(self) -> ChunkingBenchmarkResult:
        """Benchmark with small dataset (10 memories)."""
        # Create clusters of similar embeddings
        clusters = []
        for _ in range(2):  # 2 clusters
            base_embedding = np.random.rand(384)
            base_embedding = base_embedding / np.linalg.norm(base_embedding)
            clusters.append(base_embedding)

        memories = []
        for i in range(10):
            cluster_idx = i % len(clusters)
            embedding = clusters[cluster_idx] + np.random.normal(0, 0.02, 384)
            mem = self._create_memory(
                f"mem-{i}",
                f"Content item {i}" * 5,
                embedding=embedding,
            )
            memories.append(mem)

        self.service.similarity_threshold = 0.60  # Lower threshold for clustering

        start_time = time.time()
        chunks, metrics = self.service.chunk_memories(
            memories, chunk_type=ChunkType.TOPICAL
        )
        elapsed = (time.time() - start_time) * 1000

        result = ChunkingBenchmarkResult(
            benchmark_name="small_dataset",
            timestamp=datetime.now(timezone.utc),
            num_memories=len(memories),
            chunk_type=ChunkType.TOPICAL.value,
            processing_time_ms=elapsed,
            chunks_created=len(chunks),
            avg_memories_per_chunk=metrics.avg_memories_per_chunk,
            compression_ratio=metrics.compression_ratio,
            avg_cohesion_score=metrics.avg_cohesion_score,
            chunk_fragmentation=metrics.chunk_fragmentation,
        )

        self.results.append(result)
        return result

    def benchmark_medium_dataset(self) -> ChunkingBenchmarkResult:
        """Benchmark with medium dataset (50 memories)."""
        # Create clusters of similar embeddings
        clusters = []
        for _ in range(5):  # 5 clusters
            base_embedding = np.random.rand(384)
            base_embedding = base_embedding / np.linalg.norm(base_embedding)
            clusters.append(base_embedding)

        memories = []
        for i in range(50):
            cluster_idx = i % len(clusters)
            embedding = clusters[cluster_idx] + np.random.normal(0, 0.02, 384)
            mem = self._create_memory(
                f"mem-{i}",
                f"Content item {i}" * 10,
                embedding=embedding,
            )
            memories.append(mem)

        self.service.similarity_threshold = 0.60

        start_time = time.time()
        chunks, metrics = self.service.chunk_memories(
            memories, chunk_type=ChunkType.TOPICAL
        )
        elapsed = (time.time() - start_time) * 1000

        result = ChunkingBenchmarkResult(
            benchmark_name="medium_dataset",
            timestamp=datetime.now(timezone.utc),
            num_memories=len(memories),
            chunk_type=ChunkType.TOPICAL.value,
            processing_time_ms=elapsed,
            chunks_created=len(chunks),
            avg_memories_per_chunk=metrics.avg_memories_per_chunk,
            compression_ratio=metrics.compression_ratio,
            avg_cohesion_score=metrics.avg_cohesion_score,
            chunk_fragmentation=metrics.chunk_fragmentation,
        )

        self.results.append(result)
        return result

    def benchmark_large_dataset(self) -> ChunkingBenchmarkResult:
        """Benchmark with large dataset (200 memories)."""
        # Create clusters of similar embeddings
        clusters = []
        for _ in range(10):  # 10 clusters
            base_embedding = np.random.rand(384)
            base_embedding = base_embedding / np.linalg.norm(base_embedding)
            clusters.append(base_embedding)

        memories = []
        for i in range(200):
            cluster_idx = i % len(clusters)
            embedding = clusters[cluster_idx] + np.random.normal(0, 0.02, 384)
            mem = self._create_memory(
                f"mem-{i}",
                f"Content item {i}" * 15,
                embedding=embedding,
            )
            memories.append(mem)

        self.service.similarity_threshold = 0.60

        start_time = time.time()
        chunks, metrics = self.service.chunk_memories(
            memories, chunk_type=ChunkType.TOPICAL
        )
        elapsed = (time.time() - start_time) * 1000

        result = ChunkingBenchmarkResult(
            benchmark_name="large_dataset",
            timestamp=datetime.now(timezone.utc),
            num_memories=len(memories),
            chunk_type=ChunkType.TOPICAL.value,
            processing_time_ms=elapsed,
            chunks_created=len(chunks),
            avg_memories_per_chunk=metrics.avg_memories_per_chunk,
            compression_ratio=metrics.compression_ratio,
            avg_cohesion_score=metrics.avg_cohesion_score,
            chunk_fragmentation=metrics.chunk_fragmentation,
        )

        self.results.append(result)
        return result

    def benchmark_chunk_type_comparison(self) -> Dict:
        """Compare chunking across different chunk types."""
        base_embedding = np.random.rand(384)
        base_embedding = base_embedding / np.linalg.norm(base_embedding)

        memories = [
            self._create_memory(
                f"mem-{i}",
                f"Content item {i}" * 8,
                embedding=base_embedding + np.random.normal(0, 0.1, 384),
            )
            for i in range(30)
        ]

        results = {}
        for chunk_type in ChunkType:
            start_time = time.time()
            chunks, metrics = self.service.chunk_memories(
                memories, chunk_type=chunk_type
            )
            elapsed = (time.time() - start_time) * 1000

            results[chunk_type.value] = {
                "chunks_created": len(chunks),
                "avg_memories_per_chunk": metrics.avg_memories_per_chunk,
                "compression_ratio": metrics.compression_ratio,
                "avg_cohesion_score": metrics.avg_cohesion_score,
                "processing_time_ms": elapsed,
            }

        return results

    def export_results(self, filepath: str) -> None:
        """Export benchmark results to JSON file."""
        export_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_benchmarks": len(self.results),
            "results": [r.to_dict() for r in self.results],
            "summary": self._generate_summary(),
        }

        with open(filepath, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

        logger.info(f"Results exported to {filepath}")

    def _generate_summary(self) -> Dict:
        """Generate summary statistics from all results."""
        if not self.results:
            return {}

        processing_times = [r.processing_time_ms for r in self.results]
        compression_ratios = [r.compression_ratio for r in self.results]
        cohesion_scores = [r.avg_cohesion_score for r in self.results]

        return {
            "avg_processing_time_ms": float(np.mean(processing_times)),
            "max_processing_time_ms": float(np.max(processing_times)),
            "min_processing_time_ms": float(np.min(processing_times)),
            "avg_compression_ratio": float(np.mean(compression_ratios)),
            "avg_cohesion_score": float(np.mean(cohesion_scores)),
            "total_benchmarks_run": len(self.results),
        }


if __name__ == "__main__":
    benchmark = ChunkingBenchmark()
    results = benchmark.run_all_benchmarks()
    benchmark.export_results("/tmp/chunking_benchmark_results.json")

    print("\nChunking Benchmark Summary:")
    print(json.dumps(results, indent=2, default=str))
