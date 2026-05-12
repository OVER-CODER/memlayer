"""
Phase 5: Runtime Telemetry & Cognitive Observability

Core telemetry infrastructure for MemLayer's adaptive compilation runtime.
Provides token analytics, latency profiling, semantic drift analysis, and
provider benchmarking for observable cognitive runtime.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
import time
import json
from pathlib import Path


# ============================================================================
# DATA MODELS
# ============================================================================


class CompilationStage(Enum):
    """Compilation pipeline stages."""

    RETRIEVAL = "retrieval"
    DEDUPLICATION = "deduplication"
    CHUNKING = "chunking"
    COMPRESSION = "compression"
    RANKING = "ranking"
    PLANNING = "planning"
    ALLOCATION = "allocation"
    ASSEMBLY = "assembly"
    GENERATION = "generation"


@dataclass
class TokenMetrics:
    """Token consumption at a specific stage."""

    stage: str
    raw_tokens: int
    compiled_tokens: int
    compression_ratio: float
    semantic_value: float  # 0-1 quality score
    efficiency_ratio: float  # compiled_tokens / semantic_value


@dataclass
class LatencyMetric:
    """Latency measurement for a stage."""

    stage: str
    latency_ms: float
    tokens_processed: int
    ms_per_token: float
    percentile_rank: float = 0.0


@dataclass
class SemanticQualityMetric:
    """Semantic quality measurement."""

    timestamp: datetime

    # Quality dimensions
    semantic_density: float  # unique semantic concepts / total tokens
    entity_continuity: float  # named entity preservation
    reasoning_continuity: float  # logical flow preservation
    topic_preservation: float  # topic consistency
    information_retention: float  # information not lost

    # Trends
    drift_from_baseline: float  # quality change from original
    anomaly_score: float  # 0-1, where 1 = strong regression

    # Metadata
    query_length: int
    context_size: int
    compression_mode: str
    provider: str


@dataclass
class CompilationTrace:
    """Complete trace of a single compilation."""

    trace_id: str
    timestamp: datetime
    query: str
    query_complexity: str
    provider: str

    # Stages
    stages: Dict[str, "StageTrace"] = field(default_factory=dict)

    # Aggregates
    total_latency_ms: float = 0.0
    total_raw_tokens: int = 0
    total_compiled_tokens: int = 0
    final_quality_score: float = 0.0

    def to_dict(self):
        return {
            "trace_id": self.trace_id,
            "timestamp": self.timestamp.isoformat(),
            "query": self.query,
            "query_complexity": self.query_complexity,
            "provider": self.provider,
            "stages": {k: asdict(v) for k, v in self.stages.items()},
            "total_latency_ms": self.total_latency_ms,
            "total_raw_tokens": self.total_raw_tokens,
            "total_compiled_tokens": self.total_compiled_tokens,
            "final_quality_score": self.final_quality_score,
        }


@dataclass
class StageTrace:
    """Trace for a single compilation stage."""

    stage_name: str
    start_time: datetime
    end_time: datetime
    latency_ms: float

    # Tokens
    input_tokens: int
    output_tokens: int
    compression_ratio: float

    # Quality
    semantic_quality_before: float
    semantic_quality_after: float
    quality_delta: float

    # Metadata
    parameters: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)


@dataclass
class ProviderBenchmarkResult:
    """Benchmark result for a provider."""

    provider: str
    query_type: str
    compression_mode: str
    token_budget: int

    # Performance
    total_latency_ms: float
    tokens_used: int
    quality_score: float
    efficiency_ratio: float

    # Provider-specific metrics
    provider_efficiency: float
    reasoning_depth: float
    semantic_retention: float

    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BenchmarkComparison:
    """Comparison across providers and strategies."""

    benchmark_id: str
    timestamp: datetime

    # Results by provider
    results: Dict[str, List[ProviderBenchmarkResult]] = field(default_factory=dict)

    # Aggregated findings
    best_provider_by_latency: str = ""
    best_provider_by_quality: str = ""
    best_provider_by_efficiency: str = ""

    # Query-type patterns
    query_patterns: Dict[str, str] = field(default_factory=dict)


# ============================================================================
# TELEMETRY SERVICES
# ============================================================================


class TokenAnalyticsService:
    """Tracks token consumption across compilation pipeline."""

    def __init__(self):
        """Initialize token analytics."""
        self.metrics: List[TokenMetrics] = []
        self.stage_summaries: Dict[str, Dict] = {}
        self.provider_patterns: Dict[str, Dict] = {}

    def record_tokens(
        self,
        stage: str,
        raw_tokens: int,
        compiled_tokens: int,
        semantic_value: float,
    ) -> None:
        """Record token consumption at a stage."""
        compression_ratio = compiled_tokens / raw_tokens if raw_tokens > 0 else 0
        efficiency = compiled_tokens / semantic_value if semantic_value > 0 else 0

        metric = TokenMetrics(
            stage=stage,
            raw_tokens=raw_tokens,
            compiled_tokens=compiled_tokens,
            compression_ratio=compression_ratio,
            semantic_value=semantic_value,
            efficiency_ratio=efficiency,
        )
        self.metrics.append(metric)

    def get_stage_summary(self, stage: str) -> Dict:
        """Get summary statistics for a stage."""
        stage_metrics = [m for m in self.metrics if m.stage == stage]

        if not stage_metrics:
            return {}

        raw_tokens = [m.raw_tokens for m in stage_metrics]
        compiled_tokens = [m.compiled_tokens for m in stage_metrics]
        efficiency = [m.efficiency_ratio for m in stage_metrics]

        return {
            "stage": stage,
            "num_samples": len(stage_metrics),
            "avg_raw_tokens": sum(raw_tokens) / len(raw_tokens),
            "avg_compiled_tokens": sum(compiled_tokens) / len(compiled_tokens),
            "avg_compression_ratio": sum(m.compression_ratio for m in stage_metrics)
            / len(stage_metrics),
            "avg_efficiency_ratio": sum(efficiency) / len(efficiency),
            "total_tokens_saved": sum(
                r - c for r, c in zip(raw_tokens, compiled_tokens)
            ),
            "min_efficiency": min(efficiency),
            "max_efficiency": max(efficiency),
        }

    def get_provider_pattern(self, provider: str) -> Dict:
        """Analyze token patterns for a provider."""
        # This will be populated during benchmarking
        return self.provider_patterns.get(provider, {})

    def get_all_metrics(self) -> List[Dict]:
        """Export all metrics."""
        return [asdict(m) for m in self.metrics]

    def compute_savings(self) -> Dict:
        """Compute total token savings."""
        total_raw = sum(m.raw_tokens for m in self.metrics)
        total_compiled = sum(m.compiled_tokens for m in self.metrics)

        return {
            "total_raw_tokens": total_raw,
            "total_compiled_tokens": total_compiled,
            "total_saved": total_raw - total_compiled,
            "compression_ratio": total_compiled / total_raw if total_raw > 0 else 0,
            "savings_percentage": ((total_raw - total_compiled) / total_raw * 100)
            if total_raw > 0
            else 0,
        }


class LatencyProfiler:
    """Profiles and measures compilation latency."""

    def __init__(self):
        """Initialize latency profiler."""
        self.traces: List[CompilationTrace] = []
        self.stage_latencies: Dict[str, List[float]] = {}
        self.current_trace: Optional[CompilationTrace] = None
        self.stage_timers: Dict[str, float] = {}

    def start_trace(
        self, trace_id: str, query: str, query_complexity: str, provider: str
    ) -> None:
        """Start a new compilation trace."""
        self.current_trace = CompilationTrace(
            trace_id=trace_id,
            timestamp=datetime.utcnow(),
            query=query,
            query_complexity=query_complexity,
            provider=provider,
        )

    def start_stage(self, stage_name: str, input_tokens: int = 0) -> None:
        """Start timing a compilation stage."""
        if self.current_trace is None:
            return

        self.stage_timers[stage_name] = time.time()
        # Store input tokens as metadata for the stage
        if stage_name not in self.current_trace.stages:
            self.current_trace.stages[stage_name] = None

    def end_stage(
        self,
        stage_name: str,
        output_tokens: int = 0,
        quality_before: float = 1.0,
        quality_after: float = 1.0,
        **metadata,
    ) -> None:
        """End timing a compilation stage."""
        if self.current_trace is None or stage_name not in self.stage_timers:
            return

        start_time = self.stage_timers.pop(stage_name)
        elapsed = (time.time() - start_time) * 1000  # ms

        trace = StageTrace(
            stage_name=stage_name,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            latency_ms=elapsed,
            input_tokens=0,  # Will be updated
            output_tokens=output_tokens,
            compression_ratio=1.0,
            semantic_quality_before=quality_before,
            semantic_quality_after=quality_after,
            quality_delta=quality_after - quality_before,
            metadata=metadata,
        )

        self.current_trace.stages[stage_name] = trace

        # Record latency
        if stage_name not in self.stage_latencies:
            self.stage_latencies[stage_name] = []
        self.stage_latencies[stage_name].append(elapsed)

    def finish_trace(self, final_quality: float) -> Optional[CompilationTrace]:
        """Finish the current trace."""
        if self.current_trace is None:
            return None

        self.current_trace.total_latency_ms = sum(
            s.latency_ms for s in self.current_trace.stages.values()
        )
        self.current_trace.final_quality_score = final_quality

        trace = self.current_trace
        self.traces.append(trace)
        self.current_trace = None

        return trace

    def get_stage_latency_summary(self, stage: str) -> Dict:
        """Get latency summary for a stage."""
        if stage not in self.stage_latencies:
            return {}

        latencies = sorted(self.stage_latencies[stage])
        n = len(latencies)

        return {
            "stage": stage,
            "num_samples": n,
            "min_ms": latencies[0],
            "max_ms": latencies[-1],
            "avg_ms": sum(latencies) / n,
            "median_ms": latencies[n // 2],
            "p95_ms": latencies[int(n * 0.95)] if n > 0 else 0,
            "p99_ms": latencies[int(n * 0.99)] if n > 0 else 0,
        }

    def identify_bottlenecks(self) -> List[Dict]:
        """Identify slowest stages."""
        summaries = []
        for stage in self.stage_latencies.keys():
            summary = self.get_stage_latency_summary(stage)
            if summary:
                summaries.append(summary)

        # Sort by avg latency descending
        return sorted(summaries, key=lambda x: x.get("avg_ms", 0), reverse=True)

    def get_traces(self) -> List[Dict]:
        """Export all traces."""
        return [t.to_dict() for t in self.traces]


class SemanticDriftAnalyzer:
    """Analyzes semantic quality degradation."""

    def __init__(self):
        """Initialize semantic drift analyzer."""
        self.quality_samples: List[SemanticQualityMetric] = []
        self.baseline_quality: Optional[float] = None
        self.quality_trends: Dict[str, List[float]] = {}

    def record_quality(self, metric: SemanticQualityMetric) -> None:
        """Record a semantic quality measurement."""
        self.quality_samples.append(metric)

        # Update baseline on first sample
        if self.baseline_quality is None:
            self.baseline_quality = (
                metric.semantic_density * 0.25
                + metric.entity_continuity * 0.25
                + metric.reasoning_continuity * 0.25
                + metric.topic_preservation * 0.25
            )

        # Track trends
        for dimension in [
            "semantic_density",
            "entity_continuity",
            "reasoning_continuity",
            "topic_preservation",
        ]:
            value = getattr(metric, dimension)
            if dimension not in self.quality_trends:
                self.quality_trends[dimension] = []
            self.quality_trends[dimension].append(value)

    def compute_drift(self, metric: SemanticQualityMetric) -> float:
        """Compute drift from baseline."""
        if self.baseline_quality is None:
            return 0.0

        current = (
            metric.semantic_density * 0.25
            + metric.entity_continuity * 0.25
            + metric.reasoning_continuity * 0.25
            + metric.topic_preservation * 0.25
        )

        drift = (
            (self.baseline_quality - current) / self.baseline_quality
            if self.baseline_quality > 0
            else 0
        )
        return max(0, drift)

    def detect_degradation(self, threshold: float = 0.2) -> List[Dict]:
        """Detect quality degradation events."""
        degradations = []

        for i, metric in enumerate(self.quality_samples):
            drift = self.compute_drift(metric)
            if drift > threshold:
                degradations.append(
                    {
                        "index": i,
                        "timestamp": metric.timestamp.isoformat(),
                        "drift": drift,
                        "severity": "high" if drift > 0.5 else "medium",
                        "quality_dimensions": {
                            "semantic_density": metric.semantic_density,
                            "entity_continuity": metric.entity_continuity,
                            "reasoning_continuity": metric.reasoning_continuity,
                            "topic_preservation": metric.topic_preservation,
                        },
                    }
                )

        return degradations

    def get_trend_statistics(self, dimension: str) -> Dict:
        """Get statistical summary of a quality dimension trend."""
        if dimension not in self.quality_trends:
            return {}

        values = self.quality_trends[dimension]
        sorted_values = sorted(values)
        n = len(values)

        return {
            "dimension": dimension,
            "num_samples": n,
            "current": values[-1] if values else 0,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "avg": sum(values) / n,
            "median": sorted_values[n // 2] if n > 0 else 0,
            "trend": "improving"
            if values[-1] > sum(values[: n // 2]) / max(1, n // 2)
            else "degrading",
        }

    def get_quality_summary(self) -> Dict:
        """Get summary of all quality metrics."""
        return {
            "num_samples": len(self.quality_samples),
            "baseline_quality": self.baseline_quality,
            "dimensions": {
                dim: self.get_trend_statistics(dim)
                for dim in [
                    "semantic_density",
                    "entity_continuity",
                    "reasoning_continuity",
                    "topic_preservation",
                ]
            },
            "total_degradation_events": len(self.detect_degradation()),
        }


class ProviderBenchmarkingService:
    """Benchmarks provider performance across scenarios."""

    def __init__(self):
        """Initialize provider benchmarking service."""
        self.results: List[ProviderBenchmarkResult] = []
        self.comparisons: List[BenchmarkComparison] = []

    def record_result(self, result: ProviderBenchmarkResult) -> None:
        """Record a benchmark result."""
        self.results.append(result)

    def create_comparison(
        self, benchmark_id: str, results: List[ProviderBenchmarkResult]
    ) -> BenchmarkComparison:
        """Create a comparison across providers."""
        comparison = BenchmarkComparison(
            benchmark_id=benchmark_id,
            timestamp=datetime.utcnow(),
        )

        # Organize by provider
        by_provider: Dict[str, List[ProviderBenchmarkResult]] = {}
        for result in results:
            if result.provider not in by_provider:
                by_provider[result.provider] = []
            by_provider[result.provider].append(result)

        comparison.results = by_provider

        # Find best providers
        if results:
            latencies = {r.provider: r.total_latency_ms for r in results}
            qualities = {r.provider: r.quality_score for r in results}
            efficiencies = {r.provider: r.efficiency_ratio for r in results}

            comparison.best_provider_by_latency = min(latencies, key=latencies.get)
            comparison.best_provider_by_quality = max(qualities, key=qualities.get)
            comparison.best_provider_by_efficiency = max(
                efficiencies, key=efficiencies.get
            )

        self.comparisons.append(comparison)
        return comparison

    def get_provider_summary(self, provider: str) -> Dict:
        """Get performance summary for a provider."""
        provider_results = [r for r in self.results if r.provider == provider]

        if not provider_results:
            return {}

        latencies = [r.total_latency_ms for r in provider_results]
        qualities = [r.quality_score for r in provider_results]
        efficiencies = [r.efficiency_ratio for r in provider_results]

        return {
            "provider": provider,
            "num_benchmarks": len(provider_results),
            "avg_latency_ms": sum(latencies) / len(latencies),
            "avg_quality": sum(qualities) / len(qualities),
            "avg_efficiency": sum(efficiencies) / len(efficiencies),
            "min_latency": min(latencies),
            "max_latency": max(latencies),
            "min_quality": min(qualities),
            "max_quality": max(qualities),
        }

    def get_all_results(self) -> List[Dict]:
        """Export all results."""
        return [asdict(r) for r in self.results]

    def get_comparisons(self) -> List[Dict]:
        """Export all comparisons."""
        comparisons = []
        for c in self.comparisons:
            comp_dict = {
                "benchmark_id": c.benchmark_id,
                "timestamp": c.timestamp.isoformat(),
                "best_provider_by_latency": c.best_provider_by_latency,
                "best_provider_by_quality": c.best_provider_by_quality,
                "best_provider_by_efficiency": c.best_provider_by_efficiency,
                "results": {
                    provider: [asdict(r) for r in results]
                    for provider, results in c.results.items()
                },
            }
            comparisons.append(comp_dict)
        return comparisons


class RuntimeTraceSystem:
    """Complete runtime tracing for the compilation pipeline."""

    def __init__(self):
        """Initialize runtime trace system."""
        self.token_analytics = TokenAnalyticsService()
        self.latency_profiler = LatencyProfiler()
        self.semantic_drift = SemanticDriftAnalyzer()
        self.provider_benchmarking = ProviderBenchmarkingService()

        self.active_traces: Dict[str, CompilationTrace] = {}

    def export_all_telemetry(self) -> Dict:
        """Export complete telemetry snapshot."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "token_analytics": {
                "metrics": self.token_analytics.get_all_metrics(),
                "savings": self.token_analytics.compute_savings(),
                "stage_summaries": {
                    stage: self.token_analytics.get_stage_summary(stage)
                    for stage in set(m.stage for m in self.token_analytics.metrics)
                },
            },
            "latency_profiling": {
                "traces": self.latency_profiler.get_traces(),
                "bottlenecks": self.latency_profiler.identify_bottlenecks(),
                "stage_summaries": {
                    stage: self.latency_profiler.get_stage_latency_summary(stage)
                    for stage in self.latency_profiler.stage_latencies.keys()
                },
            },
            "semantic_drift": self.semantic_drift.get_quality_summary(),
            "provider_benchmarking": {
                "results": self.provider_benchmarking.get_all_results(),
                "comparisons": self.provider_benchmarking.get_comparisons(),
            },
        }

    def save_telemetry(self, output_path: str) -> None:
        """Save all telemetry to JSON file."""
        telemetry = self.export_all_telemetry()

        with open(output_path, "w") as f:
            json.dump(telemetry, f, indent=2, default=str)
