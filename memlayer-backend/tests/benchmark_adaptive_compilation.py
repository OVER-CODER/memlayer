"""
Benchmark suite for Adaptive Context Compilation Runtime (Phase 4).

Measures:
- Ranking effectiveness across different query types
- Budget allocation quality assessment
- Adaptive compression mode selection
- Provider-specific optimization validation
- Semantic retention under different constraints
- Plan creation performance
"""

import time
import json
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from unittest.mock import Mock
import sys
import logging

# Mock embedding service to avoid TensorFlow/Keras import during collection
sys.modules["app.services.embedding"] = Mock()

from app.compiler.adaptive_compilation import (
    AdaptiveCompilationPlanner,
    RelevanceRankingService,
    TokenBudgetAllocator,
    ContextQualityEvaluator,
    ContextFailureAnalyzer,
    QueryType,
    RankingFactors,
)

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""

    benchmark_name: str
    timestamp: datetime

    # Query characteristics
    query_type: str
    query_complexity: float
    num_memories: int
    token_budget: int

    # Ranking metrics
    top_1_relevance: float = 0.0
    top_5_avg_relevance: float = 0.0
    ranking_time_ms: float = 0.0

    # Budget allocation metrics
    allocation_efficiency: float = 0.0  # How well budget is used
    response_reserve_utilization: float = 0.0
    budget_breakdown: Dict = field(default_factory=dict)

    # Quality metrics
    semantic_density: float = 0.0
    redundancy_score: float = 0.0
    entity_continuity: float = 0.0
    reasoning_preservation: float = 0.0
    overall_quality: float = 0.0

    # Plan creation metrics
    plan_creation_time_ms: float = 0.0
    num_selected_memories: int = 0

    # Provider-specific metrics
    provider: str = "claude"
    provider_fit_score: float = 0.0

    def to_dict(self):
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat(),
            "budget_breakdown": self.budget_breakdown,
        }


class AdaptiveCompilationBenchmark:
    """Benchmark suite for adaptive compilation."""

    def __init__(self):
        """Initialize benchmark suite."""
        self.ranking_service = RelevanceRankingService(Mock())
        self.planner = AdaptiveCompilationPlanner(
            ranking_service=self.ranking_service, embedding_service=Mock()
        )
        self.quality_evaluator = ContextQualityEvaluator()
        self.failure_analyzer = ContextFailureAnalyzer()
        self.results: List[BenchmarkResult] = []

    def create_mock_memory(
        self,
        mem_id: str,
        content: str,
        importance: float = 0.5,
        timestamp: datetime = None,
    ) -> Mock:
        """Create a mock memory object."""
        mem = Mock()
        mem.id = mem_id
        mem.raw_content = content
        mem.importance_score = importance
        mem.timestamp = timestamp or datetime.utcnow()
        mem.embedding = np.random.random(768).tolist()
        return mem

    def run_all_benchmarks(self) -> Dict:
        """Run complete benchmark suite."""
        logger.info("Starting adaptive compilation benchmarks...")

        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "benchmarks": {
                "ranking_effectiveness": self.benchmark_ranking_effectiveness(),
                "budget_allocation_quality": self.benchmark_budget_allocation(),
                "compression_mode_selection": self.benchmark_compression_modes(),
                "provider_optimization": self.benchmark_provider_optimization(),
                "semantic_retention": self.benchmark_semantic_retention(),
                "scalability": self.benchmark_scalability(),
            },
            "summary": self.generate_summary(),
        }

        return results

    def benchmark_ranking_effectiveness(self) -> Dict:
        """Benchmark ranking service effectiveness."""
        logger.info("Running ranking effectiveness benchmark...")

        results = {}
        query_types = [
            (
                "REASONING",
                "Why does machine learning require large datasets for training?",
            ),
            ("FACTUAL", "What is the capital of France?"),
            ("CODING", "How do I use the REST API for user authentication?"),
            ("RESEARCH", "What are the latest papers on transformer architectures?"),
            ("NARRATIVE", "Tell me about the history of artificial intelligence"),
        ]

        for query_type_str, query in query_types:
            # Create diverse memories
            memories = [
                self.create_mock_memory(
                    f"mem-{i}",
                    f"Memory content {i}: " + " ".join([query] * (i % 5 + 1)),
                    importance=np.random.random(),
                    timestamp=datetime.utcnow()
                    - timedelta(days=np.random.randint(0, 100)),
                )
                for i in range(20)
            ]

            # Rank memories
            start = time.time()
            ranked = self.ranking_service.rank_memories(
                query, memories, provider_type="claude"
            )
            ranking_time = (time.time() - start) * 1000

            # Calculate metrics
            top_1_rel = ranked[0][1] if ranked else 0.0
            top_5_rel = (
                np.mean([r[1] for r in ranked[:5]])
                if len(ranked) >= 5
                else np.mean([r[1] for r in ranked])
            )

            result = BenchmarkResult(
                benchmark_name=f"ranking_{query_type_str.lower()}",
                timestamp=datetime.utcnow(),
                query_type=query_type_str,
                query_complexity=0.5,
                num_memories=len(memories),
                total_budget=4000,
                top_1_relevance=top_1_rel,
                top_5_avg_relevance=top_5_rel,
                ranking_time_ms=ranking_time,
                provider_type="claude",
            )

            results[query_type_str] = result.to_dict()
            self.results.append(result)

        return results

    def benchmark_budget_allocation(self) -> Dict:
        """Benchmark budget allocation quality."""
        logger.info("Running budget allocation benchmark...")

        results = {}
        scenarios = [
            ("low_complexity", 0.2, 50),
            ("medium_complexity", 0.5, 100),
            ("high_complexity", 0.9, 200),
        ]

        for scenario_name, complexity, memory_count in scenarios:
            memories = [
                self.create_mock_memory(f"mem-{i}", f"Content {i}")
                for i in range(memory_count)
            ]

            start = time.time()
            allocation = TokenBudgetAllocator.allocate_budget(
                total_budget=8000,
                query_complexity=complexity,
                workspace_size=memory_count,
                compression_mode="compressed",
                provider_type="claude",
            )
            alloc_time = (time.time() - start) * 1000

            # Calculate efficiency
            total_allocated = (
                allocation.reasoning_context
                + allocation.semantic_memories
                + allocation.workspace_summary
                + allocation.chunk_summaries
                + allocation.metadata_glue
                + allocation.response_reserve
            )
            efficiency = total_allocated / 8000 if total_allocated > 0 else 0.0

            result = BenchmarkResult(
                benchmark_name=f"allocation_{scenario_name}",
                timestamp=datetime.utcnow(),
                query_type="REASONING",
                query_complexity=complexity,
                num_memories=memory_count,
                total_budget=8000,
                allocation_efficiency=efficiency,
                response_reserve_utilization=allocation.response_reserve / 8000,
                budget_breakdown={
                    "reasoning_context": allocation.reasoning_context,
                    "semantic_memories": allocation.semantic_memories,
                    "workspace_summary": allocation.workspace_summary,
                    "chunk_summaries": allocation.chunk_summaries,
                    "metadata_glue": allocation.metadata_glue,
                    "response_reserve": allocation.response_reserve,
                },
                plan_creation_time_ms=alloc_time,
            )

            results[scenario_name] = result.to_dict()
            self.results.append(result)

        return results

    def benchmark_compression_modes(self) -> Dict:
        """Benchmark compression mode selection."""
        logger.info("Running compression mode selection benchmark...")

        results = {}
        modes = ["minimal", "balanced", "compressed", "aggressive"]

        for mode in modes:
            memories = [
                self.create_mock_memory(f"mem-{i}", f"Memory {i} content")
                for i in range(30)
            ]

            start = time.time()
            plan = self.planner.create_compilation_plan(
                query="Test query",
                memories=memories,
                total_budget=4000,
                compression_mode=mode,
                provider_type="claude",
            )
            plan_time = (time.time() - start) * 1000

            result = BenchmarkResult(
                benchmark_name=f"compression_{mode}",
                timestamp=datetime.utcnow(),
                query_type="REASONING",
                query_complexity=0.5,
                num_memories=len(memories),
                total_budget=4000,
                plan_creation_time_ms=plan_time,
                num_selected_memories=len(plan.selected_memories),
                provider_type="claude",
            )

            results[mode] = result.to_dict()
            self.results.append(result)

        return results

    def benchmark_provider_optimization(self) -> Dict:
        """Benchmark provider-specific optimization."""
        logger.info("Running provider optimization benchmark...")

        results = {}
        providers = ["claude", "openai", "gemini"]

        for provider in providers:
            memories = [
                self.create_mock_memory(f"mem-{i}", f"Memory {i}") for i in range(20)
            ]

            start = time.time()
            plan = self.planner.create_compilation_plan(
                query="What is machine learning?",
                memories=memories,
                total_budget=8000,
                compression_mode="balanced",
                provider=provider,
            )
            plan_time = (time.time() - start) * 1000

            # Calculate provider fit from ranking factors
            ranked = self.ranking_service.rank_memories(
                "What is machine learning?", memories, provider_type=provider
            )
            provider_fit = (
                np.mean([r[2].provider_fit for r in ranked]) if ranked else 0.0
            )

            result = BenchmarkResult(
                benchmark_name=f"provider_{provider}",
                timestamp=datetime.utcnow(),
                query_type="FACTUAL",
                query_complexity=0.3,
                num_memories=len(memories),
                total_budget=8000,
                plan_creation_time_ms=plan_time,
                num_selected_memories=len(plan.selected_memories),
                provider=provider,
                provider_fit_score=provider_fit,
            )

            results[provider] = result.to_dict()
            self.results.append(result)

        return results

    def benchmark_semantic_retention(self) -> Dict:
        """Benchmark semantic retention under different constraints."""
        logger.info("Running semantic retention benchmark...")

        results = {}

        # Test with different memory sizes and budgets
        scenarios = [
            ("small_budget_large_memory", 2000, 100),
            ("balanced_budget_memory", 4000, 50),
            ("large_budget_small_memory", 8000, 20),
        ]

        for scenario_name, budget, memory_count in scenarios:
            original_context = " ".join(
                [
                    f"Memory {i}: This is important information about topic {i % 5} "
                    for i in range(memory_count)
                ]
            )

            # Simulate compression by selecting subset
            compressed_ratio = budget / (
                len(original_context.split()) * 10
            )  # rough estimate
            compressed_context = " ".join(
                original_context.split()[
                    : int(len(original_context.split()) * compressed_ratio)
                ]
            )

            # Evaluate quality
            quality = self.quality_evaluator.evaluate_quality(
                original_context=original_context,
                compiled_context=compressed_context,
                query="Test query",
            )

            result = BenchmarkResult(
                benchmark_name=f"retention_{scenario_name}",
                timestamp=datetime.utcnow(),
                query_type="REASONING",
                query_complexity=0.5,
                num_memories=memory_count,
                total_budget=budget,
                semantic_density=quality.semantic_density,
                redundancy_score=quality.redundancy,
                entity_continuity=quality.entity_continuity,
                reasoning_preservation=quality.reasoning_preservation,
                overall_quality=quality.overall_quality,
            )

            results[scenario_name] = result.to_dict()
            self.results.append(result)

        return results

    def benchmark_scalability(self) -> Dict:
        """Benchmark scalability with increasing memory count."""
        logger.info("Running scalability benchmark...")

        results = {}
        memory_counts = [10, 50, 100, 500, 1000]

        for count in memory_counts:
            memories = [
                self.create_mock_memory(f"mem-{i}", f"Memory {i}") for i in range(count)
            ]

            start = time.time()
            plan = self.planner.create_compilation_plan(
                query="Test query",
                memories=memories,
                total_budget=8000,
                compression_mode="balanced",
                provider_type="claude",
            )
            plan_time = (time.time() - start) * 1000

            start = time.time()
            ranked = self.ranking_service.rank_memories(
                "Test query", memories, provider_type="claude"
            )
            ranking_time = (time.time() - start) * 1000

            result = BenchmarkResult(
                benchmark_name=f"scalability_{count}memories",
                timestamp=datetime.utcnow(),
                query_type="REASONING",
                query_complexity=0.5,
                num_memories=count,
                total_budget=8000,
                plan_creation_time_ms=plan_time,
                ranking_time_ms=ranking_time,
                num_selected_memories=len(plan.selected_memories),
            )

            results[f"memories_{count}"] = result.to_dict()
            self.results.append(result)

        return results

    def generate_summary(self) -> Dict:
        """Generate summary statistics."""
        if not self.results:
            return {}

        return {
            "total_benchmarks": len(self.results),
            "avg_plan_creation_time_ms": np.mean(
                [
                    r.plan_creation_time_ms
                    for r in self.results
                    if r.plan_creation_time_ms > 0
                ]
            ),
            "avg_ranking_time_ms": np.mean(
                [r.ranking_time_ms for r in self.results if r.ranking_time_ms > 0]
            ),
            "avg_overall_quality": np.mean(
                [r.overall_quality for r in self.results if r.overall_quality > 0]
            ),
            "avg_allocation_efficiency": np.mean(
                [
                    r.allocation_efficiency
                    for r in self.results
                    if r.allocation_efficiency > 0
                ]
            ),
        }

    def save_results(self, output_file: str = None) -> str:
        """Save benchmark results to JSON file."""
        if output_file is None:
            output_file = (
                f"benchmark_adaptive_compilation_{datetime.utcnow().timestamp()}.json"
            )

        results = self.run_all_benchmarks()

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Benchmark results saved to {output_file}")
        return output_file


def main():
    """Run benchmark suite."""
    benchmark = AdaptiveCompilationBenchmark()
    results = benchmark.run_all_benchmarks()

    # Print summary
    print("\n" + "=" * 80)
    print("ADAPTIVE COMPILATION BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"Total benchmarks: {results['summary']['total_benchmarks']}")
    print(
        f"Avg plan creation time: {results['summary']['avg_plan_creation_time_ms']:.2f}ms"
    )
    print(f"Avg ranking time: {results['summary']['avg_ranking_time_ms']:.2f}ms")
    print(f"Avg overall quality: {results['summary']['avg_overall_quality']:.3f}")
    print(
        f"Avg allocation efficiency: {results['summary']['avg_allocation_efficiency']:.3f}"
    )
    print("=" * 80 + "\n")

    # Save results
    benchmark.save_results()


if __name__ == "__main__":
    main()
