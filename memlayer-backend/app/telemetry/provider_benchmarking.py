"""
Provider Benchmarking Service for Phase 5.

Benchmarks and compares LLM providers (Claude, OpenAI, Gemini) across
token budgets, query complexity, compression modes, and provides
provider-specific intelligence for optimization.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class QueryComplexity(Enum):
    """Query complexity levels."""

    SIMPLE = "simple"  # < 100 tokens, single concept
    MODERATE = "moderate"  # 100-500 tokens, multiple concepts
    COMPLEX = "complex"  # 500-2000 tokens, deep reasoning
    VERY_COMPLEX = "very_complex"  # > 2000 tokens, multi-step reasoning


class ProviderStrength(Enum):
    """Provider strength indicators."""

    WEAK = "weak"  # Bottom performer
    MODERATE = "moderate"
    STRONG = "strong"
    EXCELLENT = "excellent"  # Top performer


@dataclass
class ProviderTokenMetrics:
    """Token metrics for a specific provider."""

    provider: str
    compression_mode: str
    query_complexity: QueryComplexity

    # Token stats
    avg_raw_tokens: float = 0.0
    avg_compressed_tokens: float = 0.0
    avg_compression_ratio: float = 0.0
    avg_token_efficiency: float = 0.0

    # Quality metrics
    avg_semantic_density: float = 0.0
    avg_reasoning_preservation: float = 0.0
    avg_entity_preservation: float = 0.0

    # Performance
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0

    # Benchmarks
    run_count: int = 0
    success_count: int = 0
    success_rate: float = 0.0

    def calculate_metrics(self) -> None:
        """Calculate derived metrics."""
        if self.avg_raw_tokens > 0:
            self.avg_compression_ratio = (
                self.avg_compressed_tokens / self.avg_raw_tokens
            )
        if self.run_count > 0:
            self.success_rate = self.success_count / self.run_count

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "provider": self.provider,
            "compression_mode": self.compression_mode,
            "query_complexity": self.query_complexity.value,
            "avg_raw_tokens": self.avg_raw_tokens,
            "avg_compressed_tokens": self.avg_compressed_tokens,
            "avg_compression_ratio": self.avg_compression_ratio,
            "avg_token_efficiency": self.avg_token_efficiency,
            "avg_semantic_density": self.avg_semantic_density,
            "avg_reasoning_preservation": self.avg_reasoning_preservation,
            "avg_entity_preservation": self.avg_entity_preservation,
            "avg_latency_ms": self.avg_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "run_count": self.run_count,
            "success_count": self.success_count,
            "success_rate": self.success_rate,
        }


@dataclass
class ProviderBenchmarkResult:
    """Benchmark result for a provider across various conditions."""

    benchmark_id: str
    provider: str
    timestamp: datetime

    # Test conditions
    compression_mode: str = "balanced"
    query_complexity: QueryComplexity = QueryComplexity.MODERATE
    token_budget: int = 4000

    # Results
    metrics: ProviderTokenMetrics = field(
        default_factory=lambda: ProviderTokenMetrics(
            provider="", compression_mode="", query_complexity=QueryComplexity.MODERATE
        )
    )

    # Strengths and weaknesses
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)

    # Overall performance
    overall_score: float = 0.0  # 0-100
    performance_tier: ProviderStrength = ProviderStrength.MODERATE

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "benchmark_id": self.benchmark_id,
            "provider": self.provider,
            "timestamp": self.timestamp.isoformat(),
            "compression_mode": self.compression_mode,
            "query_complexity": self.query_complexity.value,
            "token_budget": self.token_budget,
            "metrics": self.metrics.to_dict(),
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "overall_score": self.overall_score,
            "performance_tier": self.performance_tier.value,
        }


@dataclass
class ProviderComparisonResult:
    """Comparison result between providers."""

    comparison_id: str
    timestamp: datetime
    providers: List[str]

    # Conditions
    compression_mode: str = "balanced"
    query_complexity: QueryComplexity = QueryComplexity.MODERATE
    token_budget: int = 4000

    # Rankings by metric
    compression_ranking: Dict[str, int] = field(
        default_factory=dict
    )  # provider -> rank
    latency_ranking: Dict[str, int] = field(default_factory=dict)
    quality_ranking: Dict[str, int] = field(default_factory=dict)
    efficiency_ranking: Dict[str, int] = field(default_factory=dict)
    overall_ranking: Dict[str, int] = field(default_factory=dict)

    # Recommendations
    recommended_provider: Optional[str] = None
    recommendation_reason: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "comparison_id": self.comparison_id,
            "timestamp": self.timestamp.isoformat(),
            "providers": self.providers,
            "compression_mode": self.compression_mode,
            "query_complexity": self.query_complexity.value,
            "token_budget": self.token_budget,
            "compression_ranking": self.compression_ranking,
            "latency_ranking": self.latency_ranking,
            "quality_ranking": self.quality_ranking,
            "efficiency_ranking": self.efficiency_ranking,
            "overall_ranking": self.overall_ranking,
            "recommended_provider": self.recommended_provider,
            "recommendation_reason": self.recommendation_reason,
        }


class ProviderBenchmarkingService:
    """
    Provider benchmarking and intelligence service.

    Compares LLM providers across metrics, identifies strengths/weaknesses,
    and provides recommendations for provider selection.
    """

    def __init__(self, max_benchmarks: int = 10000):
        """
        Initialize provider benchmarking service.

        Args:
            max_benchmarks: Maximum benchmarks to keep in memory
        """
        self.max_benchmarks = max_benchmarks
        self.benchmarks: List[ProviderBenchmarkResult] = []
        self.comparisons: List[ProviderComparisonResult] = []

        # Provider profiles for intelligence
        self.provider_profiles: Dict[str, Dict] = {}

    def record_benchmark(
        self,
        benchmark_id: str,
        provider: str,
        compression_mode: str,
        query_complexity: QueryComplexity,
        token_budget: int,
        raw_tokens: int,
        compressed_tokens: int,
        semantic_density: float,
        reasoning_preservation: float,
        entity_preservation: float,
        latency_ms: float,
        p95_latency_ms: float,
        success: bool = True,
    ) -> ProviderBenchmarkResult:
        """Record a provider benchmark result."""
        metrics = ProviderTokenMetrics(
            provider=provider,
            compression_mode=compression_mode,
            query_complexity=query_complexity,
            avg_raw_tokens=float(raw_tokens),
            avg_compressed_tokens=float(compressed_tokens),
            avg_semantic_density=semantic_density,
            avg_reasoning_preservation=reasoning_preservation,
            avg_entity_preservation=entity_preservation,
            avg_latency_ms=latency_ms,
            p95_latency_ms=p95_latency_ms,
            run_count=1,
            success_count=1 if success else 0,
        )
        metrics.calculate_metrics()

        # Analyze strengths and weaknesses
        strengths, weaknesses = self._analyze_provider_performance(metrics)

        # Calculate overall score
        overall_score = self._calculate_provider_score(metrics)

        # Determine performance tier
        if overall_score >= 85:
            tier = ProviderStrength.EXCELLENT
        elif overall_score >= 70:
            tier = ProviderStrength.STRONG
        elif overall_score >= 50:
            tier = ProviderStrength.MODERATE
        else:
            tier = ProviderStrength.WEAK

        result = ProviderBenchmarkResult(
            benchmark_id=benchmark_id,
            provider=provider,
            timestamp=datetime.now(timezone.utc),
            compression_mode=compression_mode,
            query_complexity=query_complexity,
            token_budget=token_budget,
            metrics=metrics,
            strengths=strengths,
            weaknesses=weaknesses,
            overall_score=overall_score,
            performance_tier=tier,
        )

        self.benchmarks.append(result)

        # Trim history
        if len(self.benchmarks) > self.max_benchmarks:
            self.benchmarks = self.benchmarks[-self.max_benchmarks :]

        logger.debug(
            f"Recorded benchmark {benchmark_id}: {provider} scored {overall_score:.1f} "
            f"({tier.value})"
        )

        return result

    def compare_providers(
        self,
        comparison_id: str,
        providers: List[str],
        compression_mode: str = "balanced",
        query_complexity: QueryComplexity = QueryComplexity.MODERATE,
        token_budget: int = 4000,
        lookback_benchmarks: Optional[int] = None,
    ) -> ProviderComparisonResult:
        """Compare providers against each other."""
        # Filter relevant benchmarks
        benchmarks = self._get_relevant_benchmarks(
            providers=providers,
            compression_mode=compression_mode,
            query_complexity=query_complexity,
            token_budget=token_budget,
            lookback_benchmarks=lookback_benchmarks,
        )

        if not benchmarks:
            logger.warning(f"No benchmarks found for comparison {comparison_id}")
            return ProviderComparisonResult(
                comparison_id=comparison_id,
                timestamp=datetime.now(timezone.utc),
                providers=providers,
            )

        # Aggregate metrics by provider
        provider_stats = defaultdict(list)
        for benchmark in benchmarks:
            provider_stats[benchmark.provider].append(benchmark.metrics)

        # Calculate rankings
        compression_ranking = self._rank_by_metric(
            provider_stats, "avg_compression_ratio", lower_is_better=True
        )
        latency_ranking = self._rank_by_metric(
            provider_stats, "avg_latency_ms", lower_is_better=True
        )
        quality_ranking = self._rank_by_metric(
            provider_stats, "avg_semantic_density", lower_is_better=False
        )
        efficiency_ranking = self._rank_by_metric(
            provider_stats, "avg_token_efficiency", lower_is_better=False
        )

        # Calculate overall ranking
        overall_ranking = self._calculate_overall_ranking(
            compression_ranking, latency_ranking, quality_ranking, efficiency_ranking
        )

        # Get recommendations
        recommended_provider, reason = self._get_provider_recommendation(
            overall_ranking, provider_stats
        )

        result = ProviderComparisonResult(
            comparison_id=comparison_id,
            timestamp=datetime.now(timezone.utc),
            providers=providers,
            compression_mode=compression_mode,
            query_complexity=query_complexity,
            token_budget=token_budget,
            compression_ranking=compression_ranking,
            latency_ranking=latency_ranking,
            quality_ranking=quality_ranking,
            efficiency_ranking=efficiency_ranking,
            overall_ranking=overall_ranking,
            recommended_provider=recommended_provider,
            recommendation_reason=reason,
        )

        self.comparisons.append(result)

        logger.debug(
            f"Completed comparison {comparison_id}: "
            f"Recommended {recommended_provider} - {reason}"
        )

        return result

    def get_provider_profile(self, provider: str) -> Dict:
        """Get intelligence profile for a provider."""
        provider_benchmarks = [b for b in self.benchmarks if b.provider == provider]

        if not provider_benchmarks:
            return {"message": f"No benchmarks for provider {provider}"}

        # Calculate aggregate metrics by compression mode
        by_mode = defaultdict(list)
        for benchmark in provider_benchmarks:
            by_mode[benchmark.compression_mode].append(benchmark)

        profile = {
            "provider": provider,
            "total_benchmarks": len(provider_benchmarks),
            "by_compression_mode": {},
        }

        for mode, benchmarks in by_mode.items():
            avg_score = (
                sum(b.overall_score for b in benchmarks) / len(benchmarks)
                if benchmarks
                else 0
            )
            success_rate = (
                sum(b.metrics.success_count for b in benchmarks)
                / sum(b.metrics.run_count for b in benchmarks)
                if sum(b.metrics.run_count for b in benchmarks) > 0
                else 0
            )

            profile["by_compression_mode"][mode] = {
                "benchmarks": len(benchmarks),
                "avg_score": avg_score,
                "success_rate": success_rate,
                "avg_compression_ratio": (
                    sum(b.metrics.avg_compression_ratio for b in benchmarks)
                    / len(benchmarks)
                    if benchmarks
                    else 0
                ),
                "avg_latency_ms": (
                    sum(b.metrics.avg_latency_ms for b in benchmarks) / len(benchmarks)
                    if benchmarks
                    else 0
                ),
            }

        return profile

    def get_optimization_recommendations(
        self,
        provider: str,
        compression_mode: str,
        query_complexity: QueryComplexity,
    ) -> Dict:
        """Get optimization recommendations for a provider/mode combo."""
        relevant = [
            b
            for b in self.benchmarks
            if (
                b.provider == provider
                and b.compression_mode == compression_mode
                and b.query_complexity == query_complexity
            )
        ]

        if not relevant:
            return {"message": "No data for optimization recommendations"}

        avg_benchmark = relevant[0]  # Use first as template
        weaknesses = []
        recommendations = []

        # Analyze weaknesses
        if avg_benchmark.metrics.avg_compression_ratio > 0.7:
            weaknesses.append("Poor token compression")
            recommendations.append("Consider more aggressive compression strategies")

        if avg_benchmark.metrics.avg_latency_ms > 100:
            weaknesses.append("High latency")
            recommendations.append("Consider caching or parallel processing")

        if avg_benchmark.metrics.avg_semantic_density < 0.8:
            weaknesses.append("Low semantic density")
            recommendations.append("Implement better deduplication")

        if avg_benchmark.metrics.success_rate < 0.95:
            weaknesses.append("Reliability issues")
            recommendations.append("Implement retry logic and error handling")

        return {
            "provider": provider,
            "compression_mode": compression_mode,
            "query_complexity": query_complexity.value,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "recent_benchmarks": len(relevant),
        }

    def _analyze_provider_performance(
        self, metrics: ProviderTokenMetrics
    ) -> Tuple[List[str], List[str]]:
        """Analyze provider strengths and weaknesses."""
        strengths = []
        weaknesses = []

        if metrics.avg_compression_ratio < 0.6:
            strengths.append("Excellent compression")
        elif metrics.avg_compression_ratio > 0.8:
            weaknesses.append("Poor compression")

        if metrics.avg_latency_ms < 50:
            strengths.append("Fast execution")
        elif metrics.avg_latency_ms > 200:
            weaknesses.append("Slow execution")

        if metrics.avg_semantic_density > 0.9:
            strengths.append("High semantic quality")
        elif metrics.avg_semantic_density < 0.7:
            weaknesses.append("Low semantic quality")

        if metrics.avg_token_efficiency > 0.85:
            strengths.append("High token efficiency")
        elif metrics.avg_token_efficiency < 0.65:
            weaknesses.append("Poor token efficiency")

        if metrics.success_rate > 0.95:
            strengths.append("Reliable")
        elif metrics.success_rate < 0.85:
            weaknesses.append("Unreliable")

        return strengths, weaknesses

    def _calculate_provider_score(self, metrics: ProviderTokenMetrics) -> float:
        """Calculate overall provider score (0-100)."""
        # Weighted scoring
        compression_score = max(0, 100 - (metrics.avg_compression_ratio * 50))
        latency_score = max(0, 100 - (metrics.avg_latency_ms / 2))
        quality_score = metrics.avg_semantic_density * 100
        efficiency_score = metrics.avg_token_efficiency * 100
        reliability_score = metrics.success_rate * 100

        # Weighted average
        overall = (
            compression_score * 0.25
            + latency_score * 0.15
            + quality_score * 0.30
            + efficiency_score * 0.20
            + reliability_score * 0.10
        )

        return min(100, max(0, overall))

    def _get_relevant_benchmarks(
        self,
        providers: List[str],
        compression_mode: str,
        query_complexity: QueryComplexity,
        token_budget: int,
        lookback_benchmarks: Optional[int],
    ) -> List[ProviderBenchmarkResult]:
        """Get relevant benchmarks for comparison."""
        candidates = [
            b
            for b in self.benchmarks
            if (
                b.provider in providers
                and b.compression_mode == compression_mode
                and b.query_complexity == query_complexity
                and b.token_budget == token_budget
            )
        ]

        if lookback_benchmarks:
            candidates = candidates[-lookback_benchmarks:]

        return candidates

    def _rank_by_metric(
        self,
        provider_stats: Dict[str, List[ProviderTokenMetrics]],
        metric_name: str,
        lower_is_better: bool = True,
    ) -> Dict[str, int]:
        """Rank providers by a specific metric."""
        provider_values = {}

        for provider, metrics_list in provider_stats.items():
            if metrics_list:
                avg_value = sum(getattr(m, metric_name) for m in metrics_list) / len(
                    metrics_list
                )
                provider_values[provider] = avg_value

        # Sort for ranking
        if lower_is_better:
            sorted_providers = sorted(provider_values.items(), key=lambda x: x[1])
        else:
            sorted_providers = sorted(
                provider_values.items(), key=lambda x: x[1], reverse=True
            )

        ranking = {}
        for rank, (provider, _) in enumerate(sorted_providers, 1):
            ranking[provider] = rank

        return ranking

    def _calculate_overall_ranking(
        self,
        compression_ranking: Dict,
        latency_ranking: Dict,
        quality_ranking: Dict,
        efficiency_ranking: Dict,
    ) -> Dict[str, int]:
        """Calculate overall ranking from individual rankings."""
        all_providers = set(
            list(compression_ranking.keys())
            + list(latency_ranking.keys())
            + list(quality_ranking.keys())
            + list(efficiency_ranking.keys())
        )

        overall = {}
        for provider in all_providers:
            score = (
                compression_ranking.get(provider, 999) * 0.25
                + latency_ranking.get(provider, 999) * 0.15
                + quality_ranking.get(provider, 999) * 0.30
                + efficiency_ranking.get(provider, 999) * 0.30
            )
            overall[provider] = score

        # Convert to ranking
        sorted_providers = sorted(overall.items(), key=lambda x: x[1])
        ranking = {}
        for rank, (provider, _) in enumerate(sorted_providers, 1):
            ranking[provider] = rank

        return ranking

    def _get_provider_recommendation(
        self,
        overall_ranking: Dict[str, int],
        provider_stats: Dict[str, List[ProviderTokenMetrics]],
    ) -> Tuple[Optional[str], str]:
        """Get provider recommendation."""
        if not overall_ranking:
            return None, "No providers to recommend"

        # Get top-ranked provider
        recommended = min(overall_ranking.items(), key=lambda x: x[1])[0]

        # Generate reason
        if recommended in provider_stats:
            metrics = provider_stats[recommended]
            if metrics:
                avg_metrics = metrics[0]
                if (
                    avg_metrics.avg_compression_ratio < 0.6
                    and avg_metrics.avg_latency_ms < 100
                ):
                    reason = (
                        "Best overall performance with excellent compression and speed"
                    )
                elif avg_metrics.avg_semantic_density > 0.9:
                    reason = "Superior semantic quality"
                elif avg_metrics.avg_latency_ms < 100:
                    reason = "Fastest execution speed"
                else:
                    reason = "Best overall ranking"
            else:
                reason = "Selected as top performer"
        else:
            reason = "Selected as top performer"

        return recommended, reason

    def get_benchmarking_report(self) -> Dict:
        """Generate comprehensive benchmarking report."""
        if not self.benchmarks:
            return {"message": "No benchmarks recorded"}

        providers = set(b.provider for b in self.benchmarks)
        compression_modes = set(b.compression_mode for b in self.benchmarks)
        query_complexities = set(b.query_complexity.value for b in self.benchmarks)

        return {
            "total_benchmarks": len(self.benchmarks),
            "providers": list(providers),
            "compression_modes": list(compression_modes),
            "query_complexities": list(query_complexities),
            "provider_profiles": {p: self.get_provider_profile(p) for p in providers},
            "total_comparisons": len(self.comparisons),
        }

    def export_benchmarks(self, output_file: str) -> str:
        """Export benchmarks to JSON file."""
        report = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_benchmarks": len(self.benchmarks),
            "benchmarks": [b.to_dict() for b in self.benchmarks[-1000:]],
            "comparisons": [c.to_dict() for c in self.comparisons[-100:]],
            "report": self.get_benchmarking_report(),
        }

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Exported benchmarks to {output_file}")
        return output_file


# Global provider benchmarking service instance
_benchmarking_service: Optional[ProviderBenchmarkingService] = None


def get_benchmarking_service() -> ProviderBenchmarkingService:
    """Get or create the global benchmarking service."""
    global _benchmarking_service
    if _benchmarking_service is None:
        _benchmarking_service = ProviderBenchmarkingService()
    return _benchmarking_service
