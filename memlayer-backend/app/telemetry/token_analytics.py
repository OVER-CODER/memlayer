"""
Token Analytics Engine for Phase 5.

Tracks token usage across all compilation stages, calculates
efficiency metrics, and generates historical analysis.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class TokenAllocationMetrics:
    """Token allocation across context layers."""

    reasoning_context: int = 0
    semantic_memories: int = 0
    workspace_summary: int = 0
    chunk_summaries: int = 0
    metadata_glue: int = 0
    response_reserve: int = 0

    @property
    def total_allocated(self) -> int:
        """Total allocated tokens."""
        return (
            self.reasoning_context
            + self.semantic_memories
            + self.workspace_summary
            + self.chunk_summaries
            + self.metadata_glue
            + self.response_reserve
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class TokenMetrics:
    """Complete token metrics for a compilation run."""

    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    query: str = ""
    query_type: str = "unknown"
    provider: str = "generic"
    compression_mode: str = "balanced"

    # Counts
    raw_tokens_input: int = 0
    compressed_tokens_output: int = 0
    token_budget: int = 0

    # Savings
    tokens_saved: int = 0
    compression_ratio: float = 0.0  # compressed / raw
    efficiency_ratio: float = 0.0  # useful_info / compressed_tokens

    # Allocation
    allocation: TokenAllocationMetrics = field(default_factory=TokenAllocationMetrics)

    # Semantic value
    semantic_density: float = 0.0  # information units per token
    entity_preservation: float = 0.0  # entities preserved
    reasoning_continuity: float = 0.0  # reasoning chains preserved

    # Metadata
    memory_count: int = 0
    chunk_count: int = 0
    provider_metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "query": self.query,
            "query_type": self.query_type,
            "provider": self.provider,
            "compression_mode": self.compression_mode,
            "raw_tokens_input": self.raw_tokens_input,
            "compressed_tokens_output": self.compressed_tokens_output,
            "token_budget": self.token_budget,
            "tokens_saved": self.tokens_saved,
            "compression_ratio": self.compression_ratio,
            "efficiency_ratio": self.efficiency_ratio,
            "allocation": self.allocation.to_dict(),
            "semantic_density": self.semantic_density,
            "entity_preservation": self.entity_preservation,
            "reasoning_continuity": self.reasoning_continuity,
            "memory_count": self.memory_count,
            "chunk_count": self.chunk_count,
        }


class TokenAnalyticsService:
    """
    Comprehensive token analytics for the compiler.

    Tracks token usage, efficiency, and generates analytics reports.
    """

    def __init__(self, max_history: int = 50000):
        """Initialize token analytics."""
        self.max_history = max_history
        self.metrics: List[TokenMetrics] = []

        # Aggregates
        self.total_tokens_saved = 0
        self.total_runs = 0

    def record_metrics(self, metrics: TokenMetrics) -> None:
        """Record token metrics for a compilation run."""
        self.metrics.append(metrics)

        # Update aggregates
        self.total_tokens_saved += metrics.tokens_saved
        self.total_runs += 1

        # Trim history
        if len(self.metrics) > self.max_history:
            self.metrics = self.metrics[-self.max_history :]

        logger.debug(
            f"Recorded token metrics: {metrics.tokens_saved} tokens saved, "
            f"ratio: {metrics.compression_ratio:.3f}"
        )

    def get_average_compression_ratio(
        self,
        compression_mode: Optional[str] = None,
        provider: Optional[str] = None,
        query_type: Optional[str] = None,
        time_window_hours: Optional[int] = None,
    ) -> float:
        """Get average compression ratio with optional filters."""
        filtered = self._filter_metrics(
            compression_mode=compression_mode,
            provider=provider,
            query_type=query_type,
            time_window_hours=time_window_hours,
        )

        if not filtered:
            return 0.0

        return sum(m.compression_ratio for m in filtered) / len(filtered)

    def get_average_efficiency(
        self,
        compression_mode: Optional[str] = None,
        provider: Optional[str] = None,
        time_window_hours: Optional[int] = None,
    ) -> float:
        """Get average efficiency ratio."""
        filtered = self._filter_metrics(
            compression_mode=compression_mode,
            provider=provider,
            time_window_hours=time_window_hours,
        )

        if not filtered:
            return 0.0

        return sum(m.efficiency_ratio for m in filtered) / len(filtered)

    def get_allocation_distribution(
        self,
        compression_mode: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> Dict[str, float]:
        """Get average token allocation distribution."""
        filtered = self._filter_metrics(
            compression_mode=compression_mode,
            provider=provider,
        )

        if not filtered:
            return {}

        avg_allocation = {
            "reasoning_context": 0,
            "semantic_memories": 0,
            "workspace_summary": 0,
            "chunk_summaries": 0,
            "metadata_glue": 0,
            "response_reserve": 0,
        }

        for metric in filtered:
            allocation = metric.allocation
            avg_allocation["reasoning_context"] += allocation.reasoning_context
            avg_allocation["semantic_memories"] += allocation.semantic_memories
            avg_allocation["workspace_summary"] += allocation.workspace_summary
            avg_allocation["chunk_summaries"] += allocation.chunk_summaries
            avg_allocation["metadata_glue"] += allocation.metadata_glue
            avg_allocation["response_reserve"] += allocation.response_reserve

        count = len(filtered)
        for key in avg_allocation:
            avg_allocation[key] = avg_allocation[key] / count

        return avg_allocation

    def get_provider_comparison(self) -> Dict[str, Dict]:
        """Compare token metrics across providers."""
        providers_metrics = defaultdict(list)

        for metric in self.metrics:
            providers_metrics[metric.provider].append(metric)

        comparison = {}
        for provider, metrics in providers_metrics.items():
            if metrics:
                comparison[provider] = {
                    "runs": len(metrics),
                    "avg_compression_ratio": sum(m.compression_ratio for m in metrics)
                    / len(metrics),
                    "avg_efficiency": sum(m.efficiency_ratio for m in metrics)
                    / len(metrics),
                    "total_tokens_saved": sum(m.tokens_saved for m in metrics),
                    "avg_semantic_density": sum(m.semantic_density for m in metrics)
                    / len(metrics),
                }

        return comparison

    def get_compression_mode_comparison(self) -> Dict[str, Dict]:
        """Compare metrics across compression modes."""
        modes_metrics = defaultdict(list)

        for metric in self.metrics:
            modes_metrics[metric.compression_mode].append(metric)

        comparison = {}
        for mode, metrics in modes_metrics.items():
            if metrics:
                comparison[mode] = {
                    "runs": len(metrics),
                    "avg_compression_ratio": sum(m.compression_ratio for m in metrics)
                    / len(metrics),
                    "avg_efficiency": sum(m.efficiency_ratio for m in metrics)
                    / len(metrics),
                    "total_tokens_saved": sum(m.tokens_saved for m in metrics),
                }

        return comparison

    def get_query_type_analysis(self) -> Dict[str, Dict]:
        """Analyze metrics by query type."""
        query_metrics = defaultdict(list)

        for metric in self.metrics:
            query_metrics[metric.query_type].append(metric)

        analysis = {}
        for query_type, metrics in query_metrics.items():
            if metrics:
                analysis[query_type] = {
                    "runs": len(metrics),
                    "avg_compression_ratio": sum(m.compression_ratio for m in metrics)
                    / len(metrics),
                    "avg_efficiency": sum(m.efficiency_ratio for m in metrics)
                    / len(metrics),
                    "avg_semantic_density": sum(m.semantic_density for m in metrics)
                    / len(metrics),
                }

        return analysis

    def get_historical_trend(
        self,
        metric_name: str,
        hours: int = 24,
        bucket_size_minutes: int = 60,
    ) -> List[Tuple[str, float]]:
        """Get historical trend for a metric."""
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(hours=hours)

        recent = [m for m in self.metrics if m.timestamp >= cutoff_time]

        if not recent:
            return []

        # Bucket by time
        buckets = defaultdict(list)
        for metric in recent:
            bucket_time = metric.timestamp.replace(minute=0, second=0, microsecond=0)
            bucket_key = bucket_time.isoformat()

            if metric_name == "compression_ratio":
                buckets[bucket_key].append(metric.compression_ratio)
            elif metric_name == "efficiency":
                buckets[bucket_key].append(metric.efficiency_ratio)
            elif metric_name == "semantic_density":
                buckets[bucket_key].append(metric.semantic_density)
            elif metric_name == "tokens_saved":
                buckets[bucket_key].append(metric.tokens_saved)

        # Calculate averages
        trend = []
        for bucket_key in sorted(buckets.keys()):
            values = buckets[bucket_key]
            avg = sum(values) / len(values) if values else 0.0
            trend.append((bucket_key, avg))

        return trend

    def get_analytics_report(self) -> Dict:
        """Generate comprehensive analytics report."""
        if not self.metrics:
            return {"message": "No token metrics recorded"}

        return {
            "total_runs": self.total_runs,
            "total_metrics_recorded": len(self.metrics),
            "total_tokens_saved": self.total_tokens_saved,
            "avg_compression_ratio": self.get_average_compression_ratio(),
            "avg_efficiency": self.get_average_efficiency(),
            "allocation_distribution": self.get_allocation_distribution(),
            "provider_comparison": self.get_provider_comparison(),
            "compression_mode_comparison": self.get_compression_mode_comparison(),
            "query_type_analysis": self.get_query_type_analysis(),
            "recent_trend_compression": self.get_historical_trend(
                "compression_ratio", hours=24
            ),
        }

    def export_analytics(self, output_file: str) -> str:
        """Export analytics to JSON file."""
        report = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "metrics_count": len(self.metrics),
            "metrics": [m.to_dict() for m in self.metrics[-1000:]],  # Last 1000
            "analytics": self.get_analytics_report(),
        }

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Exported token analytics to {output_file}")
        return output_file

    def _filter_metrics(
        self,
        compression_mode: Optional[str] = None,
        provider: Optional[str] = None,
        query_type: Optional[str] = None,
        time_window_hours: Optional[int] = None,
    ) -> List[TokenMetrics]:
        """Filter metrics based on criteria."""
        filtered = self.metrics[:]

        if compression_mode:
            filtered = [m for m in filtered if m.compression_mode == compression_mode]

        if provider:
            filtered = [m for m in filtered if m.provider == provider]

        if query_type:
            filtered = [m for m in filtered if m.query_type == query_type]

        if time_window_hours:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
            filtered = [m for m in filtered if m.timestamp >= cutoff_time]

        return filtered


# Global token analytics service instance
_token_analytics: Optional[TokenAnalyticsService] = None


def get_token_analytics() -> TokenAnalyticsService:
    """Get or create the global token analytics service."""
    global _token_analytics
    if _token_analytics is None:
        _token_analytics = TokenAnalyticsService()
    return _token_analytics
