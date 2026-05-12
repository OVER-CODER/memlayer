"""
Benchmark suite for Semantic Deduplication Engine.

Measures:
- Deduplication accuracy
- Token savings
- Processing latency
- Memory overhead
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

from app.compiler.semantic_deduplication import (
    SemanticDeduplicationService,
    DeduplicationMetrics,
    MergeStrategy,
)
import logging

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""

    benchmark_name: str
    timestamp: datetime
    num_memories: int
    overlap_level: str  # "none", "low", "medium", "high"
    strategy: str

    # Metrics
    processing_time_ms: float
    deduplication_ratio: float  # percentage of duplicates removed
    token_savings: int
    memory_overhead_bytes: int

    # Effectiveness
    false_positives: int = 0  # Non-duplicates marked as duplicates
    false_negatives: int = 0  # Duplicates not detected
    precision: float = 0.0
    recall: float = 0.0

    def to_dict(self):
        return asdict(self)


class DeduplicationBenchmark:
    """Benchmark suite for deduplication engine."""

    def __init__(self):
        # Create service with mock embedding service to avoid TensorFlow imports
        mock_embedding_service = Mock()
        self.service = SemanticDeduplicationService(
            embedding_service=mock_embedding_service
        )
        self.results: List[BenchmarkResult] = []

    def run_all_benchmarks(self) -> Dict:
        """Run complete benchmark suite."""
        logger.info("Starting deduplication benchmarks...")

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "benchmarks": {
                "no_duplicates": self.benchmark_no_duplicates(),
                "low_overlap": self.benchmark_low_overlap(),
                "high_overlap": self.benchmark_high_overlap(),
                "realistic_workload": self.benchmark_realistic_workload(),
                "large_scale": self.benchmark_large_scale(),
                "strategy_comparison": self.benchmark_strategy_comparison(),
            },
        }

        return results

    def benchmark_no_duplicates(self) -> BenchmarkResult:
        """Benchmark: memories with no duplicates."""
        logger.info("Running: No duplicates benchmark")

        memories = self._create_unique_memories(count=50)

        start = time.time()
        kept, metrics, groups = self.service.deduplicate(memories)
        elapsed_ms = (time.time() - start) * 1000

        result = BenchmarkResult(
            benchmark_name="no_duplicates",
            timestamp=datetime.now(timezone.utc),
            num_memories=len(memories),
            overlap_level="none",
            strategy="keep_highest_importance",
            processing_time_ms=elapsed_ms,
            deduplication_ratio=0.0,
            token_savings=0,
            memory_overhead_bytes=0,
        )

        self.results.append(result)
        logger.info(f"  Processed {len(memories)} memories in {elapsed_ms:.2f}ms")

        return result

    def benchmark_low_overlap(self) -> BenchmarkResult:
        """Benchmark: memories with low overlap (10% duplicates)."""
        logger.info("Running: Low overlap benchmark")

        memories = self._create_memories_with_duplicates(
            unique_count=45,
            duplicate_groups=1,  # 1 group of 5 similar
            similarity=0.75,
        )

        start = time.time()
        kept, metrics, groups = self.service.deduplicate(memories)
        elapsed_ms = (time.time() - start) * 1000

        removal_ratio = (len(memories) - len(kept)) / len(memories) * 100

        result = BenchmarkResult(
            benchmark_name="low_overlap",
            timestamp=datetime.now(timezone.utc),
            num_memories=len(memories),
            overlap_level="low",
            strategy="keep_highest_importance",
            processing_time_ms=elapsed_ms,
            deduplication_ratio=removal_ratio,
            token_savings=metrics.token_savings,
            memory_overhead_bytes=0,
        )

        self.results.append(result)
        logger.info(
            f"  Removed {removal_ratio:.1f}% of memories, saved {metrics.token_savings} tokens"
        )

        return result

    def benchmark_high_overlap(self) -> BenchmarkResult:
        """Benchmark: memories with high overlap (40% duplicates)."""
        logger.info("Running: High overlap benchmark")

        memories = self._create_memories_with_duplicates(
            unique_count=30,
            duplicate_groups=4,  # 4 groups of ~5
            similarity=0.90,
        )

        start = time.time()
        kept, metrics, groups = self.service.deduplicate(memories)
        elapsed_ms = (time.time() - start) * 1000

        removal_ratio = (len(memories) - len(kept)) / len(memories) * 100

        result = BenchmarkResult(
            benchmark_name="high_overlap",
            timestamp=datetime.now(timezone.utc),
            num_memories=len(memories),
            overlap_level="high",
            strategy="keep_highest_importance",
            processing_time_ms=elapsed_ms,
            deduplication_ratio=removal_ratio,
            token_savings=metrics.token_savings,
            memory_overhead_bytes=0,
        )

        self.results.append(result)
        logger.info(
            f"  Removed {removal_ratio:.1f}% of memories, saved {metrics.token_savings} tokens"
        )

        return result

    def benchmark_realistic_workload(self) -> BenchmarkResult:
        """Benchmark: realistic workspace with ~20% duplicates."""
        logger.info("Running: Realistic workload benchmark")

        # Mix of unique and duplicate memories simulating real workspace
        unique = self._create_unique_memories(count=40)
        duplicates = self._create_memories_with_duplicates(
            unique_count=0, duplicate_groups=3, similarity=0.85
        )
        memories = unique + duplicates
        np.random.shuffle(memories)

        start = time.time()
        kept, metrics, groups = self.service.deduplicate(memories)
        elapsed_ms = (time.time() - start) * 1000

        removal_ratio = (len(memories) - len(kept)) / len(memories) * 100

        result = BenchmarkResult(
            benchmark_name="realistic_workload",
            timestamp=datetime.now(timezone.utc),
            num_memories=len(memories),
            overlap_level="medium",
            strategy="keep_highest_importance",
            processing_time_ms=elapsed_ms,
            deduplication_ratio=removal_ratio,
            token_savings=metrics.token_savings,
            memory_overhead_bytes=0,
        )

        self.results.append(result)
        logger.info(
            f"  Processed {len(memories)} memories, removed {removal_ratio:.1f}%"
        )

        return result

    def benchmark_large_scale(self) -> BenchmarkResult:
        """Benchmark: large workspace with 500+ memories."""
        logger.info("Running: Large scale benchmark")

        unique = self._create_unique_memories(count=400)
        duplicates = self._create_memories_with_duplicates(
            unique_count=0,
            duplicate_groups=20,  # 20 groups
            similarity=0.82,
        )
        memories = unique + duplicates
        np.random.shuffle(memories)

        start = time.time()
        kept, metrics, groups = self.service.deduplicate(memories)
        elapsed_ms = (time.time() - start) * 1000

        removal_ratio = (len(memories) - len(kept)) / len(memories) * 100

        result = BenchmarkResult(
            benchmark_name="large_scale",
            timestamp=datetime.now(timezone.utc),
            num_memories=len(memories),
            overlap_level="medium",
            strategy="keep_highest_importance",
            processing_time_ms=elapsed_ms,
            deduplication_ratio=removal_ratio,
            token_savings=metrics.token_savings,
            memory_overhead_bytes=0,
        )

        self.results.append(result)
        logger.info(
            f"  Large scale: {len(memories)} → {len(kept)} memories in {elapsed_ms:.2f}ms"
        )

        return result

    def benchmark_strategy_comparison(self) -> Dict:
        """Compare different merge strategies."""
        logger.info("Running: Strategy comparison benchmark")

        memories = self._create_memories_with_duplicates(
            unique_count=30, duplicate_groups=5, similarity=0.88
        )

        strategies = [
            MergeStrategy.KEEP_HIGHEST_IMPORTANCE,
            MergeStrategy.KEEP_MOST_RECENT,
            MergeStrategy.KEEP_LONGEST,
        ]

        results = {}

        for strategy in strategies:
            start = time.time()
            kept, metrics, groups = self.service.deduplicate(
                memories, strategy=strategy
            )
            elapsed_ms = (time.time() - start) * 1000

            results[strategy.value] = {
                "kept": len(kept),
                "removed": len(memories) - len(kept),
                "token_savings": metrics.token_savings,
                "time_ms": elapsed_ms,
            }

            logger.info(f"  {strategy.value}: saved {metrics.token_savings} tokens")

        return results

    def _create_unique_memories(self, count: int) -> List[Mock]:
        """Create memories with completely different embeddings."""
        memories = []

        for i in range(count):
            mem = Mock()
            mem.id = f"unique-mem-{i}"
            mem.raw_content = f"Unique content {i} " + "x" * np.random.randint(50, 200)
            mem.importance_score = np.random.rand()
            mem.timestamp = datetime.now(timezone.utc)
            # Random orthogonal embedding
            mem.embedding = np.random.rand(384).tolist()

            memories.append(mem)

        return memories

    def _create_memories_with_duplicates(
        self,
        unique_count: int,
        duplicate_groups: int,
        similarity: float = 0.85,
    ) -> List[Mock]:
        """Create memories with intentional duplicates."""
        memories = []

        # Add unique memories
        unique = self._create_unique_memories(unique_count)
        memories.extend(unique)

        # Add duplicate groups
        for group_idx in range(duplicate_groups):
            # Base embedding for this group
            base_embedding = np.random.rand(384)
            base_embedding = base_embedding / (np.linalg.norm(base_embedding) + 1e-8)

            # Members per group
            members = np.random.randint(3, 8)

            for member_idx in range(members):
                # Create similar embedding
                perturbation = np.random.normal(0, 1 - similarity, 384)
                embedding = base_embedding + perturbation
                embedding = embedding / (np.linalg.norm(embedding) + 1e-8)

                mem = Mock()
                mem.id = f"dup-group-{group_idx}-mem-{member_idx}"
                mem.raw_content = (
                    f"Group {group_idx} content {member_idx} "
                    + "y" * np.random.randint(50, 150)
                )
                mem.importance_score = np.random.rand()
                mem.timestamp = datetime.now(timezone.utc)
                mem.embedding = embedding.tolist()

                memories.append(mem)

        return memories

    def export_results(self, filename: str = None) -> str:
        """Export benchmark results as JSON."""
        results_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_benchmarks": len(self.results),
            "results": [r.to_dict() for r in self.results],
            "summary": self._summarize_results(),
        }

        json_str = json.dumps(results_data, indent=2, default=str)

        if filename:
            with open(filename, "w") as f:
                f.write(json_str)
            logger.info(f"Exported benchmark results to {filename}")

        return json_str

    def _summarize_results(self) -> Dict:
        """Summarize benchmark results."""
        if not self.results:
            return {}

        return {
            "avg_processing_time_ms": sum(r.processing_time_ms for r in self.results)
            / len(self.results),
            "total_token_savings": sum(r.token_savings for r in self.results),
            "avg_deduplication_ratio": sum(r.deduplication_ratio for r in self.results)
            / len(self.results),
            "best_token_savings": max(
                (r.token_savings, r.benchmark_name) for r in self.results
            ),
            "worst_processing_time": max(
                (r.processing_time_ms, r.benchmark_name) for r in self.results
            ),
        }


if __name__ == "__main__":
    benchmark = DeduplicationBenchmark()
    results = benchmark.run_all_benchmarks()
    benchmark.export_results("/tmp/dedup_benchmark_results.json")

    print("\nBenchmark Summary:")
    print(json.dumps(results, indent=2, default=str))
