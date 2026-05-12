"""
Comprehensive tests for Phase 5 telemetry and observability system.

Tests cover:
- Token analytics accuracy
- Latency profiling consistency
- Semantic drift detection
- Provider benchmarking reproducibility
- Runtime trace system correctness
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.compiler.telemetry import (
    TokenAnalyticsService,
    LatencyProfiler,
    SemanticDriftAnalyzer,
    ProviderBenchmarkingService,
    RuntimeTraceSystem,
    TokenMetrics,
    SemanticQualityMetric,
    ProviderBenchmarkResult,
    CompilationStage,
)


# ============================================================================
# TOKEN ANALYTICS TESTS
# ============================================================================


class TestTokenAnalyticsService:
    """Test token analytics functionality."""

    @pytest.fixture
    def analytics(self):
        """Create analytics service."""
        return TokenAnalyticsService()

    def test_record_tokens(self, analytics):
        """Test recording token metrics."""
        analytics.record_tokens(
            stage="deduplication",
            raw_tokens=1000,
            compiled_tokens=500,
            semantic_value=0.9,
        )

        assert len(analytics.metrics) == 1
        metric = analytics.metrics[0]
        assert metric.stage == "deduplication"
        assert metric.raw_tokens == 1000
        assert metric.compiled_tokens == 500
        assert metric.compression_ratio == 0.5

    def test_compression_ratio_calculation(self, analytics):
        """Test compression ratio is calculated correctly."""
        analytics.record_tokens("chunking", 2000, 800, 0.85)

        metric = analytics.metrics[0]
        assert metric.compression_ratio == pytest.approx(0.4)

    def test_efficiency_ratio_calculation(self, analytics):
        """Test efficiency ratio is calculated correctly."""
        analytics.record_tokens("compression", 1000, 400, 0.8)

        metric = analytics.metrics[0]
        # efficiency = 400 / 0.8 = 500
        assert metric.efficiency_ratio == pytest.approx(500.0)

    def test_stage_summary(self, analytics):
        """Test stage summary aggregation."""
        analytics.record_tokens("deduplication", 1000, 500, 0.9)
        analytics.record_tokens("deduplication", 2000, 1000, 0.85)
        analytics.record_tokens("deduplication", 1500, 750, 0.88)

        summary = analytics.get_stage_summary("deduplication")

        assert summary["stage"] == "deduplication"
        assert summary["num_samples"] == 3
        assert summary["avg_raw_tokens"] == pytest.approx(1500.0)
        assert summary["avg_compiled_tokens"] == pytest.approx(750.0)
        assert (
            summary["total_tokens_saved"] == 2250
        )  # (1000-500) + (2000-1000) + (1500-750)

    def test_compute_savings(self, analytics):
        """Test total token savings computation."""
        analytics.record_tokens("deduplication", 1000, 600, 0.9)
        analytics.record_tokens("chunking", 600, 500, 0.88)
        analytics.record_tokens("compression", 500, 250, 0.85)

        savings = analytics.compute_savings()

        assert savings["total_raw_tokens"] == 2100
        assert savings["total_compiled_tokens"] == 1350
        assert savings["total_saved"] == 750
        assert savings["savings_percentage"] == pytest.approx(35.71, rel=0.01)

    def test_export_metrics(self, analytics):
        """Test metrics export."""
        analytics.record_tokens("deduplication", 1000, 500, 0.9)

        metrics = analytics.get_all_metrics()

        assert len(metrics) == 1
        assert metrics[0]["stage"] == "deduplication"
        assert metrics[0]["raw_tokens"] == 1000


# ============================================================================
# LATENCY PROFILER TESTS
# ============================================================================


class TestLatencyProfiler:
    """Test latency profiling functionality."""

    @pytest.fixture
    def profiler(self):
        """Create latency profiler."""
        return LatencyProfiler()

    def test_start_and_end_stage(self, profiler):
        """Test starting and ending a stage."""
        profiler.start_trace("trace-1", "test query", "simple", "claude")
        profiler.start_stage("retrieval", 100)

        time.sleep(0.01)  # Sleep 10ms

        profiler.end_stage(
            "retrieval", output_tokens=50, quality_before=1.0, quality_after=0.98
        )
        trace = profiler.finish_trace(0.98)

        assert trace.trace_id == "trace-1"
        assert len(trace.stages) == 1
        assert "retrieval" in trace.stages

        stage = trace.stages["retrieval"]
        assert stage.latency_ms >= 10  # At least 10ms
        assert stage.output_tokens == 50

    def test_stage_latency_tracking(self, profiler):
        """Test latency tracking for stages."""
        profiler.start_trace("trace-1", "test", "simple", "claude")

        for i in range(3):
            profiler.start_stage("retrieval")
            time.sleep(0.005)
            profiler.end_stage("retrieval", output_tokens=100)

        profiler.finish_trace(0.95)

        summary = profiler.get_stage_latency_summary("retrieval")

        assert summary["num_samples"] == 3
        assert summary["avg_ms"] >= 5  # Average at least 5ms
        assert summary["min_ms"] > 0
        assert summary["max_ms"] >= summary["min_ms"]

    def test_identify_bottlenecks(self, profiler):
        """Test bottleneck identification."""
        profiler.start_trace("trace-1", "test", "complex", "claude")

        # Slow retrieval
        profiler.start_stage("retrieval")
        time.sleep(0.02)
        profiler.end_stage("retrieval")

        # Fast ranking
        profiler.start_stage("ranking")
        time.sleep(0.002)
        profiler.end_stage("ranking")

        profiler.finish_trace(0.9)

        bottlenecks = profiler.identify_bottlenecks()

        assert len(bottlenecks) == 2
        assert bottlenecks[0]["stage"] == "retrieval"  # Slowest first

    def test_percentile_calculations(self, profiler):
        """Test percentile calculations."""
        profiler.start_trace("trace-1", "test", "simple", "claude")

        # Record latencies from 1ms to 10ms
        for i in range(10):
            profiler.start_stage("deduplication")
            time.sleep((i + 1) * 0.001)
            profiler.end_stage("deduplication")

        profiler.finish_trace(0.9)

        summary = profiler.get_stage_latency_summary("deduplication")

        assert summary["p95_ms"] > summary["median_ms"]
        assert summary["p99_ms"] >= summary["p95_ms"]

    def test_quality_tracking(self, profiler):
        """Test quality tracking across stages."""
        profiler.start_trace("trace-1", "test", "moderate", "openai")

        profiler.start_stage("compression")
        time.sleep(0.005)
        profiler.end_stage("compression", quality_before=0.95, quality_after=0.92)

        trace = profiler.finish_trace(0.92)

        assert trace.stages["compression"].quality_delta == pytest.approx(-0.03)


# ============================================================================
# SEMANTIC DRIFT ANALYZER TESTS
# ============================================================================


class TestSemanticDriftAnalyzer:
    """Test semantic drift detection."""

    @pytest.fixture
    def analyzer(self):
        """Create drift analyzer."""
        return SemanticDriftAnalyzer()

    def test_baseline_establishment(self, analyzer):
        """Test baseline quality establishment."""
        metric = SemanticQualityMetric(
            timestamp=datetime.utcnow(),
            semantic_density=0.9,
            entity_continuity=0.88,
            reasoning_continuity=0.85,
            topic_preservation=0.92,
            information_retention=0.9,
            drift_from_baseline=0.0,
            anomaly_score=0.0,
            query_length=10,
            context_size=1000,
            compression_mode="compressed",
            provider="claude",
        )

        analyzer.record_quality(metric)

        assert analyzer.baseline_quality is not None
        assert analyzer.baseline_quality > 0

    def test_drift_detection(self, analyzer):
        """Test drift detection from baseline."""
        # First metric (baseline)
        metric1 = SemanticQualityMetric(
            timestamp=datetime.utcnow(),
            semantic_density=0.9,
            entity_continuity=0.9,
            reasoning_continuity=0.9,
            topic_preservation=0.9,
            information_retention=0.9,
            drift_from_baseline=0.0,
            anomaly_score=0.0,
            query_length=10,
            context_size=1000,
            compression_mode="compressed",
            provider="claude",
        )

        analyzer.record_quality(metric1)

        # Degraded metric
        metric2 = SemanticQualityMetric(
            timestamp=datetime.utcnow(),
            semantic_density=0.6,  # Significant drop
            entity_continuity=0.6,
            reasoning_continuity=0.6,
            topic_preservation=0.6,
            information_retention=0.6,
            drift_from_baseline=0.33,
            anomaly_score=0.7,
            query_length=10,
            context_size=1000,
            compression_mode="compressed",
            provider="claude",
        )

        drift = analyzer.compute_drift(metric2)
        assert drift > 0.25

    def test_degradation_detection(self, analyzer):
        """Test degradation event detection."""
        # Healthy metrics
        for i in range(5):
            metric = SemanticQualityMetric(
                timestamp=datetime.utcnow() + timedelta(seconds=i),
                semantic_density=0.85 + i * 0.01,
                entity_continuity=0.85,
                reasoning_continuity=0.85,
                topic_preservation=0.85,
                information_retention=0.85,
                drift_from_baseline=0.0,
                anomaly_score=0.0,
                query_length=10,
                context_size=1000,
                compression_mode="compressed",
                provider="claude",
            )
            analyzer.record_quality(metric)

        # Degraded metric
        degraded = SemanticQualityMetric(
            timestamp=datetime.utcnow() + timedelta(seconds=10),
            semantic_density=0.5,
            entity_continuity=0.5,
            reasoning_continuity=0.5,
            topic_preservation=0.5,
            information_retention=0.5,
            drift_from_baseline=0.4,
            anomaly_score=0.8,
            query_length=10,
            context_size=1000,
            compression_mode="compressed",
            provider="claude",
        )
        analyzer.record_quality(degraded)

        degradations = analyzer.detect_degradation(threshold=0.2)

        assert len(degradations) >= 1
        assert degradations[-1]["severity"] in [
            "high",
            "medium",
        ]  # Could be either depending on drift calculation

    def test_trend_statistics(self, analyzer):
        """Test trend statistics computation."""
        values = [0.9, 0.88, 0.86, 0.84, 0.82, 0.80]

        for i, value in enumerate(values):
            metric = SemanticQualityMetric(
                timestamp=datetime.utcnow() + timedelta(seconds=i),
                semantic_density=value,
                entity_continuity=value,
                reasoning_continuity=value,
                topic_preservation=value,
                information_retention=value,
                drift_from_baseline=0.0,
                anomaly_score=0.0,
                query_length=10,
                context_size=1000,
                compression_mode="compressed",
                provider="claude",
            )
            analyzer.record_quality(metric)

        trend = analyzer.get_trend_statistics("semantic_density")

        assert trend["num_samples"] == 6
        assert trend["trend"] == "degrading"  # Values are decreasing
        assert trend["min"] == 0.80
        assert trend["max"] == 0.90


# ============================================================================
# PROVIDER BENCHMARKING TESTS
# ============================================================================


class TestProviderBenchmarkingService:
    """Test provider benchmarking functionality."""

    @pytest.fixture
    def benchmarking(self):
        """Create benchmarking service."""
        return ProviderBenchmarkingService()

    def test_record_result(self, benchmarking):
        """Test recording benchmark results."""
        result = ProviderBenchmarkResult(
            provider="claude",
            query_type="simple",
            compression_mode="compressed",
            token_budget=4096,
            total_latency_ms=250.5,
            tokens_used=2048,
            quality_score=0.92,
            efficiency_ratio=0.85,
            provider_efficiency=0.88,
            reasoning_depth=0.9,
            semantic_retention=0.91,
        )

        benchmarking.record_result(result)

        assert len(benchmarking.results) == 1
        assert benchmarking.results[0].provider == "claude"

    def test_provider_summary(self, benchmarking):
        """Test provider performance summary."""
        for i in range(3):
            result = ProviderBenchmarkResult(
                provider="claude",
                query_type="moderate",
                compression_mode="compressed",
                token_budget=4096,
                total_latency_ms=200 + i * 50,
                tokens_used=2000,
                quality_score=0.90 + i * 0.01,
                efficiency_ratio=0.85,
                provider_efficiency=0.88,
                reasoning_depth=0.9,
                semantic_retention=0.91,
            )
            benchmarking.record_result(result)

        summary = benchmarking.get_provider_summary("claude")

        assert summary["num_benchmarks"] == 3
        assert summary["avg_latency_ms"] == pytest.approx(250.0)
        assert summary["avg_quality"] > 0.90

    def test_create_comparison(self, benchmarking):
        """Test comparison creation across providers."""
        results = []

        for provider in ["claude", "openai", "gemini"]:
            result = ProviderBenchmarkResult(
                provider=provider,
                query_type="complex",
                compression_mode="compressed",
                token_budget=4096,
                total_latency_ms=200
                if provider == "claude"
                else 250
                if provider == "openai"
                else 220,
                tokens_used=2000,
                quality_score=0.92
                if provider == "claude"
                else 0.88
                if provider == "openai"
                else 0.90,
                efficiency_ratio=0.85,
                provider_efficiency=0.88,
                reasoning_depth=0.9,
                semantic_retention=0.91,
            )
            results.append(result)

        comparison = benchmarking.create_comparison("bench-1", results)

        assert comparison.best_provider_by_latency == "claude"
        assert comparison.best_provider_by_quality == "claude"
        assert len(comparison.results) == 3


# ============================================================================
# RUNTIME TRACE SYSTEM TESTS
# ============================================================================


class TestRuntimeTraceSystem:
    """Test complete runtime tracing system."""

    @pytest.fixture
    def trace_system(self):
        """Create runtime trace system."""
        return RuntimeTraceSystem()

    def test_integrated_tracing(self, trace_system):
        """Test integrated tracing of compilation."""
        # Token tracking
        trace_system.token_analytics.record_tokens("retrieval", 1000, 950, 0.95)
        trace_system.token_analytics.record_tokens("deduplication", 950, 700, 0.92)
        trace_system.token_analytics.record_tokens("compression", 700, 350, 0.88)

        # Latency tracking
        trace_system.latency_profiler.start_trace(
            "trace-1", "test query", "moderate", "claude"
        )

        trace_system.latency_profiler.start_stage("retrieval", 1000)
        time.sleep(0.005)
        trace_system.latency_profiler.end_stage(
            "retrieval", output_tokens=950, quality_before=1.0, quality_after=0.98
        )

        trace_system.latency_profiler.start_stage("deduplication", 950)
        time.sleep(0.003)
        trace_system.latency_profiler.end_stage(
            "deduplication", output_tokens=700, quality_before=0.98, quality_after=0.95
        )

        trace = trace_system.latency_profiler.finish_trace(0.95)

        # Semantic quality
        quality = SemanticQualityMetric(
            timestamp=datetime.utcnow(),
            semantic_density=0.88,
            entity_continuity=0.90,
            reasoning_continuity=0.87,
            topic_preservation=0.89,
            information_retention=0.88,
            drift_from_baseline=0.0,
            anomaly_score=0.0,
            query_length=3,
            context_size=2000,
            compression_mode="compressed",
            provider="claude",
        )
        trace_system.semantic_drift.record_quality(quality)

        # Verify all systems have data
        telemetry = trace_system.export_all_telemetry()

        assert len(telemetry["token_analytics"]["metrics"]) == 3
        assert len(telemetry["latency_profiling"]["traces"]) == 1
        assert telemetry["semantic_drift"]["num_samples"] == 1

    def test_telemetry_export(self, trace_system):
        """Test complete telemetry export."""
        trace_system.token_analytics.record_tokens("retrieval", 1000, 950, 0.95)

        telemetry = trace_system.export_all_telemetry()

        assert "token_analytics" in telemetry
        assert "latency_profiling" in telemetry
        assert "semantic_drift" in telemetry
        assert "provider_benchmarking" in telemetry
        assert "timestamp" in telemetry


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestTelemetryIntegration:
    """Integration tests for complete telemetry system."""

    def test_complete_compilation_trace(self):
        """Test tracing a complete compilation pipeline."""
        trace_system = RuntimeTraceSystem()

        # Simulate full compilation
        stages = [
            ("retrieval", 1000, 950),
            ("deduplication", 950, 700),
            ("chunking", 700, 650),
            ("compression", 650, 325),
            ("ranking", 325, 320),
            ("planning", 320, 315),
            ("allocation", 315, 310),
            ("assembly", 310, 310),
        ]

        trace_system.latency_profiler.start_trace(
            "trace-compile", "complex query", "complex", "claude"
        )

        current_quality = 1.0
        for stage_name, input_tokens, output_tokens in stages:
            trace_system.token_analytics.record_tokens(
                stage_name, input_tokens, output_tokens, current_quality
            )

            trace_system.latency_profiler.start_stage(stage_name, input_tokens)
            time.sleep(0.001)
            current_quality *= 0.98  # Simulate slight quality degradation
            trace_system.latency_profiler.end_stage(
                stage_name,
                output_tokens=output_tokens,
                quality_before=current_quality / 0.98,
                quality_after=current_quality,
            )

        trace = trace_system.latency_profiler.finish_trace(current_quality)

        # Verify trace structure
        assert trace.trace_id == "trace-compile"
        assert len(trace.stages) == 8
        assert trace.total_latency_ms > 0

        # Verify token savings
        savings = trace_system.token_analytics.compute_savings()
        assert savings["total_saved"] == 690  # 4570 - 3880
        assert savings["savings_percentage"] > 10  # Around 15% savings


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
