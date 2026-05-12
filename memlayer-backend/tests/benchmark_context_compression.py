"""
Benchmark suite for Context Compression Engine (Phase 3).

Measures:
- Compression ratio across all modes
- Semantic retention (entity, topic, reasoning)
- Latency and performance
- Provider-optimized compression effectiveness
- Token budget adherence
- Compression stability
"""

import time
import json
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from unittest.mock import Mock
import sys
import os

# Mock embedding service
sys.modules["app.services.embedding"] = Mock()

from app.compiler.context_compression import (
    ContextCompressionService,
    CompressionMode,
    ProviderType,
    TokenBudgetSimulator,
)
import logging

logger = logging.getLogger(__name__)


@dataclass
class CompressionBenchmarkResult:
    """Result of a single compression benchmark."""

    benchmark_name: str
    timestamp: datetime

    # Input characteristics
    content_length: int
    original_tokens: int

    # Compression settings
    compression_mode: str
    provider_type: str
    token_budget: int = 0

    # Results
    compressed_tokens: int = 0
    compression_ratio: float = 0.0
    compression_time_ms: float = 0.0

    # Semantic preservation
    semantic_retention: float = 0.0
    entity_retention: float = 0.0
    topic_retention: float = 0.0
    reasoning_continuity: float = 0.0

    # Quality
    budget_compliance: float = 0.0  # How well budget was met

    def to_dict(self):
        return asdict(self)


class CompressionBenchmark:
    """Benchmark suite for compression engine."""

    def __init__(self):
        """Initialize benchmark suite."""
        mock_embedding_service = Mock()
        self.compression_service = ContextCompressionService(
            embedding_service=mock_embedding_service
        )
        self.results: List[CompressionBenchmarkResult] = []

    def run_all_benchmarks(self) -> Dict:
        """Run complete compression benchmark suite."""
        logger.info("Starting compression benchmarks...")

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "benchmarks": {
                "mode_comparison": self.benchmark_mode_comparison(),
                "provider_comparison": self.benchmark_provider_comparison(),
                "token_budget_compliance": self.benchmark_token_budget_compliance(),
                "semantic_retention": self.benchmark_semantic_retention(),
                "scalability": self.benchmark_scalability(),
            },
        }

        return results

    def _generate_content(self, length: str) -> str:
        """Generate benchmark content."""
        base_content = """
        The advancement of artificial intelligence has transformed multiple domains including 
        healthcare, finance, and scientific research. Large language models have achieved 
        remarkable capabilities in natural language understanding and generation. These models 
        are trained on diverse data sources including books, academic papers, and web content.
        The transformer architecture with attention mechanisms enables processing of long-range 
        dependencies in text. Scaling laws show that model performance improves predictably with 
        size. Recent work has focused on improving efficiency, reducing latency, and enhancing 
        factual accuracy. Safety and alignment considerations are crucial for deployment.
        """

        if length == "small":
            return base_content
        elif length == "medium":
            return base_content * 3
        elif length == "large":
            return base_content * 10
        else:
            return base_content

    def benchmark_mode_comparison(self) -> Dict:
        """Compare compression across all modes."""
        content = self._generate_content("medium")

        results_by_mode = {}

        for mode in CompressionMode:
            start_time = time.time()
            compressed = self.compression_service.compress_context(
                content, mode=mode, provider=ProviderType.GENERIC
            )
            elapsed = (time.time() - start_time) * 1000

            result = CompressionBenchmarkResult(
                benchmark_name=f"mode_{mode.value}",
                timestamp=datetime.now(timezone.utc),
                content_length=len(content),
                original_tokens=compressed.original_tokens,
                compression_mode=mode.value,
                provider_type=ProviderType.GENERIC.value,
                compressed_tokens=compressed.compressed_tokens,
                compression_ratio=compressed.compression_ratio,
                compression_time_ms=elapsed,
                semantic_retention=compressed.semantic_retention,
                entity_retention=compressed.entity_retention,
                topic_retention=compressed.topic_retention,
                reasoning_continuity=compressed.reasoning_continuity,
            )

            self.results.append(result)

            results_by_mode[mode.value] = {
                "compression_ratio": compressed.compression_ratio,
                "semantic_retention": compressed.semantic_retention,
                "compression_time_ms": elapsed,
            }

        return results_by_mode

    def benchmark_provider_comparison(self) -> Dict:
        """Compare provider-aware compression."""
        content = self._generate_content("medium")

        results_by_provider = {}

        for provider in ProviderType:
            start_time = time.time()
            compressed = self.compression_service.compress_context(
                content,
                mode=CompressionMode.COMPRESSED,
                provider=provider,
            )
            elapsed = (time.time() - start_time) * 1000

            result = CompressionBenchmarkResult(
                benchmark_name=f"provider_{provider.value}",
                timestamp=datetime.now(timezone.utc),
                content_length=len(content),
                original_tokens=compressed.original_tokens,
                compression_mode=CompressionMode.COMPRESSED.value,
                provider_type=provider.value,
                compressed_tokens=compressed.compressed_tokens,
                compression_ratio=compressed.compression_ratio,
                compression_time_ms=elapsed,
                semantic_retention=compressed.semantic_retention,
                reasoning_continuity=compressed.reasoning_continuity,
            )

            self.results.append(result)

            results_by_provider[provider.value] = {
                "compression_ratio": compressed.compression_ratio,
                "semantic_retention": compressed.semantic_retention,
                "reasoning_continuity": compressed.reasoning_continuity,
                "compression_time_ms": elapsed,
            }

        return results_by_provider

    def benchmark_token_budget_compliance(self) -> Dict:
        """Test token budget compliance."""
        content = self._generate_content("large")
        original_tokens = len(content) // 4

        budgets = [500, 1000, 2000, 4000]
        results_by_budget = {}

        for budget in budgets:
            start_time = time.time()
            compressed = self.compression_service.compress_context(
                content,
                mode=CompressionMode.MINIMAL,
                provider=ProviderType.CLAUDE,
                token_budget=budget,
            )
            elapsed = (time.time() - start_time) * 1000

            # Calculate budget compliance (how close to budget)
            if budget > 0:
                budget_compliance = 1.0 - (
                    abs(compressed.compressed_tokens - budget) / budget
                )
                budget_compliance = max(0.0, min(budget_compliance, 1.0))
            else:
                budget_compliance = 1.0

            result = CompressionBenchmarkResult(
                benchmark_name=f"budget_{budget}",
                timestamp=datetime.now(timezone.utc),
                content_length=len(content),
                original_tokens=original_tokens,
                compression_mode=CompressionMode.MINIMAL.value,
                provider_type=ProviderType.CLAUDE.value,
                token_budget=budget,
                compressed_tokens=compressed.compressed_tokens,
                compression_ratio=compressed.compression_ratio,
                compression_time_ms=elapsed,
                budget_compliance=budget_compliance,
            )

            self.results.append(result)

            results_by_budget[str(budget)] = {
                "target_budget": budget,
                "actual_tokens": compressed.compressed_tokens,
                "budget_compliance": budget_compliance,
                "compression_ratio": compressed.compression_ratio,
            }

        return results_by_budget

    def benchmark_semantic_retention(self) -> Dict:
        """Test semantic retention across different content types."""
        content_types = {
            "technical": """
            The neural network uses ReLU activation functions and batch normalization. 
            The loss function is computed using torch.nn.CrossEntropyLoss(). Training 
            involves backpropagation through the network using Adam optimizer with 
            learning_rate=0.001. The model architecture consists of 3 conv layers 
            followed by 2 fully connected layers. Dropout with p=0.5 is applied 
            to prevent overfitting.
            """,
            "logical": """
            Because the model shows high accuracy, therefore we should deploy it. 
            If the budget allows, then we can add more features. Since performance 
            improves with scale, thus we should consider larger training sets. 
            This means the implementation is justified.
            """,
            "narrative": """
            Alice worked on machine learning for three years. She published papers 
            on neural networks and transformers. Bob joined her research group and 
            contributed to optimizing training. Together they developed a new 
            compression technique. Their work was presented at major conferences.
            """,
        }

        results_by_type = {}

        for content_type, content in content_types.items():
            compressed = self.compression_service.compress_context(
                content, mode=CompressionMode.COMPRESSED
            )

            result = CompressionBenchmarkResult(
                benchmark_name=f"content_{content_type}",
                timestamp=datetime.now(timezone.utc),
                content_length=len(content),
                original_tokens=compressed.original_tokens,
                compression_mode=CompressionMode.COMPRESSED.value,
                provider_type=ProviderType.GENERIC.value,
                compressed_tokens=compressed.compressed_tokens,
                compression_ratio=compressed.compression_ratio,
                semantic_retention=compressed.semantic_retention,
                entity_retention=compressed.entity_retention,
                topic_retention=compressed.topic_retention,
                reasoning_continuity=compressed.reasoning_continuity,
            )

            self.results.append(result)

            results_by_type[content_type] = {
                "semantic_retention": compressed.semantic_retention,
                "entity_retention": compressed.entity_retention,
                "topic_retention": compressed.topic_retention,
                "reasoning_continuity": compressed.reasoning_continuity,
                "compression_ratio": compressed.compression_ratio,
            }

        return results_by_type

    def benchmark_scalability(self) -> Dict:
        """Test scalability with increasing content size."""
        sizes = {
            "small": self._generate_content("small"),
            "medium": self._generate_content("medium"),
            "large": self._generate_content("large"),
        }

        results_by_size = {}

        for size_name, content in sizes.items():
            original_tokens = len(content) // 4

            start_time = time.time()
            compressed = self.compression_service.compress_context(
                content, mode=CompressionMode.COMPRESSED
            )
            elapsed = (time.time() - start_time) * 1000

            # Calculate compression speed (tokens per ms)
            compression_speed = original_tokens / elapsed if elapsed > 0 else 0

            result = CompressionBenchmarkResult(
                benchmark_name=f"size_{size_name}",
                timestamp=datetime.now(timezone.utc),
                content_length=len(content),
                original_tokens=original_tokens,
                compression_mode=CompressionMode.COMPRESSED.value,
                provider_type=ProviderType.GENERIC.value,
                compressed_tokens=compressed.compressed_tokens,
                compression_ratio=compressed.compression_ratio,
                compression_time_ms=elapsed,
            )

            self.results.append(result)

            results_by_size[size_name] = {
                "original_tokens": original_tokens,
                "compressed_tokens": compressed.compressed_tokens,
                "compression_time_ms": elapsed,
                "tokens_per_ms": compression_speed,
                "compression_ratio": compressed.compression_ratio,
            }

        return results_by_size

    def export_results(self, filepath: str) -> None:
        """Export benchmark results to JSON."""
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
        """Generate summary statistics."""
        if not self.results:
            return {}

        compression_ratios = [r.compression_ratio for r in self.results]
        retention_scores = [
            r.semantic_retention for r in self.results if r.semantic_retention > 0
        ]
        times = [r.compression_time_ms for r in self.results]

        return {
            "total_benchmarks": len(self.results),
            "avg_compression_ratio": float(
                sum(compression_ratios) / len(compression_ratios)
            ),
            "best_compression_ratio": float(max(compression_ratios)),
            "worst_compression_ratio": float(min(compression_ratios)),
            "avg_semantic_retention": float(
                sum(retention_scores) / len(retention_scores) if retention_scores else 0
            ),
            "avg_compression_time_ms": float(sum(times) / len(times)),
        }


if __name__ == "__main__":
    benchmark = CompressionBenchmark()
    results = benchmark.run_all_benchmarks()
    benchmark.export_results("/tmp/compression_benchmark_results.json")

    print("\nCompression Benchmark Summary:")
    print(json.dumps(results, indent=2, default=str))
