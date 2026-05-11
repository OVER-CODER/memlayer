"""
Benchmark suite for Adaptive Compilation Runtime (Phase 4).

Measures:
- Adaptive compilation planning across different query complexities
- Ranking effectiveness with multi-factor scoring
- Token budget allocation correctness per provider
- Context quality evaluation accuracy
- Provider-specific optimization effectiveness
- Compilation plan generation performance
"""

import time
import json
from typing import List, Dict, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from unittest.mock import Mock
import sys
import os

# Mock embedding service
sys.modules["app.services.embedding"] = Mock()

from app.compiler.adaptive_compilation import (
    AdaptiveCompilationPlanner,
    RelevanceRankingService,
    TokenBudgetAllocator,
    ContextQualityEvaluator,
    ContextFailureAnalyzer,
    QueryComplexity,
)
import logging

logger = logging.getLogger(__name__)


@dataclass
class CompilationBenchmarkResult:
    """Result of a single adaptive compilation benchmark."""

    benchmark_name: str
    timestamp: datetime

    # Input characteristics
    query_length: int
    query_complexity: str
    num_memories: int
    token_budget: int
    provider: str

    # Ranking results
    ranking_time_ms: float = 0.0
    avg_ranking_score: float = 0.0
    top_memory_similarity: float = 0.0

    # Allocation results
    allocation_time_ms: float = 0.0
    allocated_tokens: Dict[str, int] = field(default_factory=dict)
    allocation_accuracy: float = 0.0  # How close to budget

    # Quality results
    quality_score: float = 0.0
    entity_continuity: float = 0.0
    reasoning_preservation: float = 0.0
    compression_mode: str = ""

    # Planning results
    planning_time_ms: float = 0.0
    plan_validity: bool = False

    def to_dict(self):
        return asdict(self)


class AdaptiveCompilationBenchmark:
    """Benchmark suite for adaptive compilation engine."""

    def __init__(self):
        """Initialize benchmark suite."""
        mock_embedding_service = Mock()
        self.ranking_service = RelevanceRankingService(
            embedding_service=mock_embedding_service
        )
        self.allocator = TokenBudgetAllocator()
        self.evaluator = ContextQualityEvaluator()
        self.failure_analyzer = ContextFailureAnalyzer()
        self.planner = AdaptiveCompilationPlanner(
            ranking_service=self.ranking_service,
            allocator=self.allocator,
            quality_evaluator=self.evaluator,
            failure_analyzer=self.failure_analyzer,
        )
        self.results: List[CompilationBenchmarkResult] = []

    def run_all_benchmarks(self) -> Dict:
        """Run complete adaptive compilation benchmark suite."""
        logger.info("Starting adaptive compilation benchmarks...")

        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "benchmarks": {
                "mode_comparison": self.benchmark_mode_comparison(),
                "provider_comparison": self.benchmark_provider_comparison(),
                "token_budget_compliance": self.benchmark_token_budget_compliance(),
                "semantic_retention": self.benchmark_semantic_retention(),
                "scalability": self.benchmark_scalability(),
            },
            "summary": self._generate_summary(),
        }

        return results

    def _generate_mock_memories(self, count: int) -> List[Mock]:
        """Generate mock memory objects for benchmarking."""
        memories = []
        for i in range(count):
            mem = Mock()
            mem.id = f"mem-{i}"
            mem.content = f"Memory {i}: This is a sample memory about AI and machine learning concepts."
            mem.embedding = [0.1 * (i % 10)] * 384  # Mock embedding
            mem.timestamp = datetime.utcnow() - timedelta(hours=i)
            mem.importance = 0.5 + (0.1 * (i % 5))
            memories.append(mem)
        return memories

    def _generate_queries(self) -> Dict[str, str]:
        """Generate queries of different complexities."""
        return {
            "simple": "What is AI?",
            "moderate": "Explain how machine learning and neural networks work",
            "complex": "How do transformer-based language models achieve state-of-the-art results in "
            + "natural language processing tasks with attention mechanisms?",
            "research": "Can you provide a comprehensive analysis of "
            + " ".join(["models"] * 50),
        }

    def benchmark_mode_comparison(self) -> Dict:
        """Compare compilation across different scenarios."""
        logger.info("Benchmarking: Mode Comparison")

        queries = self._generate_queries()
        modes_tested = []

        for query_type, query in queries.items():
            memories = self._generate_mock_memories(10)

            # Measure planning time and quality
            start = time.time()
            plan = self.planner.plan_compilation(
                query=query, memories=memories, token_budget=4096, provider="claude"
            )
            planning_time = (time.time() - start) * 1000

            # Evaluate compression mode chosen
            mode_result = {
                "query_type": query_type,
                "query_length": len(query.split()),
                "compression_mode": plan.get("compression_mode", "unknown"),
                "query_complexity": plan.get("query_complexity", "unknown"),
                "planning_time_ms": planning_time,
                "memories_included": len(plan.get("ranked_memories", [])),
            }
            modes_tested.append(mode_result)
            logger.info(f"  {query_type}: {mode_result['compression_mode']} mode")

        return {"modes_tested": modes_tested}

    def benchmark_provider_comparison(self) -> Dict:
        """Compare token allocation across providers."""
        logger.info("Benchmarking: Provider Comparison")

        providers = ["claude", "openai", "gemini"]
        memories = self._generate_mock_memories(15)
        query = "Explain how machine learning works"
        token_budget = 4096

        provider_results = []

        for provider in providers:
            start = time.time()
            allocation = self.allocator.allocate_tokens(
                token_budget=token_budget,
                memories=memories,
                compression_mode="compressed",
                provider=provider,
            )
            allocation_time = (time.time() - start) * 1000

            # Calculate allocation percentages
            total_allocated = sum(allocation.values())
            percentages = {
                k: v / total_allocated if total_allocated > 0 else 0
                for k, v in allocation.items()
            }

            result = {
                "provider": provider,
                "allocation": allocation,
                "percentages": percentages,
                "allocation_time_ms": allocation_time,
                "total_allocated": total_allocated,
                "budget_accuracy": (
                    (token_budget - total_allocated) / token_budget * 100
                    if token_budget > 0
                    else 0
                ),
            }
            provider_results.append(result)
            logger.info(
                f"  {provider}: {percentages.get('active_reasoning', 0) * 100:.0f}% reasoning, "
                f"{percentages.get('semantic_memories', 0) * 100:.0f}% memories"
            )

        return {"provider_allocations": provider_results}

    def benchmark_token_budget_compliance(self) -> Dict:
        """Test token budget compliance across different budgets."""
        logger.info("Benchmarking: Token Budget Compliance")

        budgets = [500, 1000, 2000, 4096, 8192]
        memories = self._generate_mock_memories(20)
        query = "Tell me about advanced machine learning techniques"

        compliance_results = []

        for budget in budgets:
            plan = self.planner.plan_compilation(
                query=query, memories=memories, token_budget=budget, provider="claude"
            )

            allocation = self.allocator.allocate_tokens(
                token_budget=budget,
                memories=memories,
                compression_mode=plan.get("compression_mode", "compressed"),
                provider="claude",
            )

            total_allocated = sum(allocation.values())
            compliance_pct = 100 - (abs(budget - total_allocated) / budget * 100)

            result = {
                "token_budget": budget,
                "total_allocated": total_allocated,
                "compliance_percentage": max(0, compliance_pct),
                "compression_mode": plan.get("compression_mode", "unknown"),
                "variance": abs(budget - total_allocated),
            }
            compliance_results.append(result)
            logger.info(f"  Budget {budget}: {compliance_pct:.1f}% compliance")

        return {"budget_compliance": compliance_results}

    def benchmark_semantic_retention(self) -> Dict:
        """Test semantic retention across content types."""
        logger.info("Benchmarking: Semantic Retention")

        memories = self._generate_mock_memories(10)
        query = "How do neural networks learn?"

        # Evaluate quality with mock compiled context
        mock_context = {
            "active_reasoning": "How do neural networks learn? They learn through backpropagation.",
            "semantic_memories": " ".join([m.content for m in memories[:3]]),
            "summary": "Overview of neural networks",
        }

        start = time.time()
        quality = self.evaluator.evaluate_context(
            context=mock_context, query=query, provider="claude"
        )
        evaluation_time = (time.time() - start) * 1000

        result = {
            "query": query,
            "evaluation_time_ms": evaluation_time,
            "quality_score": quality.get("overall_score", 0),
            "semantic_density": quality.get("semantic_density", 0),
            "entity_continuity": quality.get("entity_continuity", 0),
            "reasoning_preservation": quality.get("reasoning_preservation", 0),
            "provider_compatibility": quality.get("provider_compatibility", 0),
        }
        logger.info(f"  Quality score: {result['quality_score']:.2f}")

        return {"semantic_retention": result}

    def benchmark_scalability(self) -> Dict:
        """Test scalability with different memory counts."""
        logger.info("Benchmarking: Scalability")

        memory_counts = [5, 10, 20, 50, 100]
        query = "Explain gradient descent in machine learning"
        scalability_results = []

        for count in memory_counts:
            memories = self._generate_mock_memories(count)

            # Measure ranking time
            start = time.time()
            ranked = self.ranking_service.rank_memories(memories, query)
            ranking_time = (time.time() - start) * 1000

            # Measure planning time
            start = time.time()
            plan = self.planner.plan_compilation(
                query=query, memories=memories, token_budget=4096, provider="claude"
            )
            planning_time = (time.time() - start) * 1000

            result = {
                "memory_count": count,
                "ranking_time_ms": ranking_time,
                "planning_time_ms": planning_time,
                "total_time_ms": ranking_time + planning_time,
                "avg_time_per_memory_ms": (ranking_time + planning_time) / count,
            }
            scalability_results.append(result)
            logger.info(f"  {count} memories: {result['total_time_ms']:.2f}ms total")

        return {"scalability": scalability_results}

    def _generate_summary(self) -> Dict:
        """Generate summary statistics from all benchmarks."""
        summary = {
            "total_benchmarks_run": len(self.results),
            "total_time_seconds": sum(r.planning_time_ms for r in self.results) / 1000,
            "avg_planning_time_ms": (
                sum(r.planning_time_ms for r in self.results) / len(self.results)
                if self.results
                else 0
            ),
        }
        return summary


def run_benchmarks():
    """Run benchmark suite and save results."""
    benchmark = AdaptiveCompilationBenchmark()
    results = benchmark.run_all_benchmarks()

    # Save to file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = f"benchmark_results_phase4_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Benchmark results saved to {output_file}")
    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    results = run_benchmarks()
    print("\n" + "=" * 80)
    print("PHASE 4 ADAPTIVE COMPILATION BENCHMARKS COMPLETE")
    print("=" * 80)
