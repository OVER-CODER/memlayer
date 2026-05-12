"""
Comprehensive test suite for Phase 5 telemetry services.

Tests RuntimeTraceService, TokenAnalyticsService, LatencyProfiler,
and SemanticDriftAnalyzer with realistic scenarios.
"""

import pytest
from datetime import datetime, timedelta
from app.telemetry import (
    RuntimeTraceService,
    TokenAnalyticsService,
    LatencyProfiler,
    SemanticDriftAnalyzer,
    ProviderBenchmarkingService,
    TraceStage,
    SemanticMetrics,
    TokenMetrics,
    TokenAllocationMetrics,
    LatencyLevel,
    DriftLevel,
    EntityDriftMetrics,
    ReasoningContinuityMetrics,
    QueryComplexity,
    ProviderStrength,
)


class TestRuntimeTraceService:
    """Test runtime trace service."""

    def test_create_and_finalize_execution_trace(self):
        """Test creating and finalizing an execution trace."""
        service = RuntimeTraceService()

        # Start execution
        trace = service.start_execution(
            query="What is the capital of France?",
            query_type="geography",
            provider="claude",
            compression_mode="balanced",
            token_budget=4000,
            input_memories_count=5,
        )

        assert trace is not None
        assert trace.query == "What is the capital of France?"
        assert trace.query_type == "geography"
        assert trace.provider == "claude"
        assert trace.input_memories_count == 5

        # Record stages
        service.record_stage(
            stage=TraceStage.RETRIEVAL,
            duration_ms=10.5,
            input_token_count=1000,
            output_token_count=950,
            semantic_metrics=SemanticMetrics(
                semantic_density=0.95, entity_continuity=0.98
            ),
        )

        service.record_stage(
            stage=TraceStage.COMPRESSION,
            duration_ms=20.3,
            input_token_count=950,
            output_token_count=500,
            compression_ratio=0.526,
        )

        assert len(service.current_trace.stages) == 2

        # Finalize
        final_trace = service.finalize_execution(
            success=True,
            output_context_tokens=500,
            overall_quality_score=0.92,
            semantic_retention=0.88,
        )

        assert final_trace.success
        assert final_trace.output_context_tokens == 500
        assert final_trace.overall_quality_score == 0.92
        assert final_trace.total_token_savings == 500  # 1000 - 500

    def test_trace_statistics(self):
        """Test getting trace statistics."""
        service = RuntimeTraceService()

        # Create multiple traces
        for i in range(5):
            trace = service.start_execution(
                query=f"Query {i}",
                provider="claude",
                compression_mode="balanced",
            )

            service.record_stage(
                stage=TraceStage.RETRIEVAL,
                duration_ms=10.0 + i,
                input_token_count=1000,
                output_token_count=900,
            )

            service.finalize_execution(
                success=(i < 4),  # Last one fails
                overall_quality_score=0.9 - (i * 0.05),
            )

        stats = service.get_trace_statistics()

        assert stats["total_traces"] == 5
        assert stats["successful_traces"] == 4
        assert stats["failed_traces"] == 1
        assert stats["success_rate"] == 0.8


class TestTokenAnalyticsService:
    """Test token analytics service."""

    def test_record_and_filter_metrics(self):
        """Test recording and filtering token metrics."""
        service = TokenAnalyticsService()

        # Record metrics for different providers
        for provider in ["claude", "openai", "gemini"]:
            metrics = TokenMetrics(
                query="Test query",
                query_type="test",
                provider=provider,
                compression_mode="balanced",
                raw_tokens_input=1000,
                compressed_tokens_output=600,
                token_budget=4000,
                tokens_saved=400,
                compression_ratio=0.6,
                efficiency_ratio=0.85,
                semantic_density=0.92,
            )
            service.record_metrics(metrics)

        # Filter by provider
        assert service.get_average_compression_ratio(provider="claude") > 0
        assert len(service.metrics) == 3

    def test_provider_comparison(self):
        """Test provider comparison."""
        service = TokenAnalyticsService()

        providers = ["claude", "openai", "gemini"]
        for provider in providers:
            for i in range(3):
                metrics = TokenMetrics(
                    query=f"Query {i}",
                    provider=provider,
                    compression_mode="balanced",
                    raw_tokens_input=1000,
                    compressed_tokens_output=600 + (i * 10),
                    tokens_saved=400 - (i * 10),
                    compression_ratio=0.6,
                    efficiency_ratio=0.85,
                )
                service.record_metrics(metrics)

        comparison = service.get_provider_comparison()

        assert len(comparison) == 3
        assert all(p in comparison for p in providers)
        assert all("runs" in comparison[p] for p in providers)

    def test_analytics_report(self):
        """Test generating analytics report."""
        service = TokenAnalyticsService()

        # Record metrics with different compression modes
        for mode in ["aggressive", "balanced", "conservative"]:
            metrics = TokenMetrics(
                compression_mode=mode,
                raw_tokens_input=1000,
                compressed_tokens_output=500 if mode == "aggressive" else 700,
                compression_ratio=0.5 if mode == "aggressive" else 0.7,
            )
            service.record_metrics(metrics)

        report = service.get_analytics_report()

        assert "total_runs" in report
        assert "provider_comparison" in report
        assert "compression_mode_comparison" in report


class TestLatencyProfiler:
    """Test latency profiler."""

    def test_create_and_finalize_profile(self):
        """Test creating and finalizing a latency profile."""
        profiler = LatencyProfiler()

        # Create profile
        profile = profiler.create_profile(
            profile_id="test-1",
            provider="claude",
            compression_mode="balanced",
            query_type="coding",
        )

        # Record stage latencies
        profiler.record_stage_latency(
            profile=profile,
            stage_name="retrieval",
            duration_ms=15.5,
            input_size_items=100,
            output_size_items=95,
        )

        profiler.record_stage_latency(
            profile=profile,
            stage_name="compression",
            duration_ms=50.2,
            input_size_items=95,
            output_size_items=50,
        )

        profiler.record_stage_latency(
            profile=profile,
            stage_name="generation",
            duration_ms=25.1,
            input_size_items=50,
            output_size_items=50,
        )

        # Finalize profile
        profiler.finalize_profile(profile)

        assert profile.total_duration_ms > 0
        assert profile.bottleneck_stage is not None
        assert profile.bottleneck_percentage > 0

    def test_percentile_calculations(self):
        """Test percentile calculations."""
        profiler = LatencyProfiler()

        # Create multiple profiles with stage latencies
        latencies = [10, 15, 20, 25, 30, 35, 40, 45, 50, 100]  # Sorted

        for i, latency in enumerate(latencies):
            profile = profiler.create_profile(profile_id=f"test-{i}")
            profiler.record_stage_latency(
                profile=profile,
                stage_name="compression",
                duration_ms=float(latency),
            )
            profiler.finalize_profile(profile)

        percentiles = profiler.get_stage_percentiles("compression")

        assert percentiles.count == 10
        assert percentiles.min == 10.0
        assert percentiles.max == 100.0
        assert (
            25 <= percentiles.p50 <= 35
        )  # Median (between 30 and 35 from our sorted list)
        assert percentiles.p95 > percentiles.p50

    def test_bottleneck_analysis(self):
        """Test bottleneck analysis."""
        profiler = LatencyProfiler()

        # Create profiles with different bottleneck stages
        for i in range(3):
            profile = profiler.create_profile(profile_id=f"test-{i}")

            if i == 0:
                # Bottleneck is retrieval
                profiler.record_stage_latency(profile, "retrieval", 100.0)
                profiler.record_stage_latency(profile, "compression", 20.0)
            elif i == 1:
                # Bottleneck is compression
                profiler.record_stage_latency(profile, "retrieval", 20.0)
                profiler.record_stage_latency(profile, "compression", 100.0)
            else:
                # Bottleneck is generation
                profiler.record_stage_latency(profile, "retrieval", 20.0)
                profiler.record_stage_latency(profile, "generation", 100.0)

            profiler.finalize_profile(profile)

        analysis = profiler.get_bottleneck_analysis()

        assert "bottlenecks" in analysis
        assert len(analysis["bottlenecks"]) > 0

    def test_latency_classification(self):
        """Test latency classification."""
        profiler = LatencyProfiler()

        test_cases = [
            (5.0, LatencyLevel.EXCELLENT),
            (25.0, LatencyLevel.GOOD),
            (100.0, LatencyLevel.ACCEPTABLE),
            (500.0, LatencyLevel.SLOW),
            (2000.0, LatencyLevel.VERY_SLOW),
        ]

        for i, (latency, expected_level) in enumerate(test_cases):
            profile = profiler.create_profile(profile_id=f"test-{i}")
            profiler.record_stage_latency(profile, "test_stage", latency)
            profiler.finalize_profile(profile)

            stage_latencies = profile.stages[0]
            assert stage_latencies.stage_level == expected_level


class TestSemanticDriftAnalyzer:
    """Test semantic drift analyzer."""

    def test_create_and_finalize_session(self):
        """Test creating and finalizing a drift session."""
        analyzer = SemanticDriftAnalyzer()

        # Create session
        session = analyzer.create_session(
            session_id="drift-1",
            query="Long document analysis",
            query_type="analysis",
            provider="claude",
            compression_mode="aggressive",
        )

        assert session.session_id == "drift-1"
        assert session.query_type == "analysis"

        # Record compression cycles with degradation
        for cycle in range(1, 4):
            entity_metrics = EntityDriftMetrics(cycle)
            entity_metrics.entities_input = 100
            entity_metrics.entities_preserved = 100 - (cycle * 10)
            entity_metrics.entities_lost = cycle * 10
            entity_metrics.calculate_preservation_ratio()

            reasoning_metrics = ReasoningContinuityMetrics(cycle)
            reasoning_metrics.reasoning_chains_input = 50
            reasoning_metrics.reasoning_chains_preserved = 50 - (cycle * 5)
            reasoning_metrics.reasoning_chains_broken = cycle * 5
            reasoning_metrics.calculate_continuity()

            analyzer.record_cycle(
                cycle_number=cycle,
                compression_ratio=0.5 + (cycle * 0.1),
                semantic_density_before=1.0,
                semantic_density_after=1.0 - (cycle * 0.05),
                entity_metrics=entity_metrics,
                reasoning_metrics=reasoning_metrics,
                topic_preservation=0.95 - (cycle * 0.05),
                reasoning_preservation=0.90 - (cycle * 0.05),
            )

        assert len(analyzer.current_session.cycles) == 3

        # Finalize session
        final_session = analyzer.finalize_session()

        assert final_session.total_degradation > 0
        assert final_session.cumulative_entity_loss > 0
        assert final_session.max_drift_level in [
            DriftLevel.STABLE,
            DriftLevel.MINOR,
            DriftLevel.MODERATE,
            DriftLevel.SIGNIFICANT,
            DriftLevel.CRITICAL,
        ]

    def test_drift_classification(self):
        """Test drift level classification."""
        analyzer = SemanticDriftAnalyzer()

        test_cases = [
            (0.02, DriftLevel.STABLE),  # 2%
            (0.10, DriftLevel.MINOR),  # 10%
            (0.20, DriftLevel.MODERATE),  # 20%
            (0.40, DriftLevel.SIGNIFICANT),  # 40%
            (0.70, DriftLevel.CRITICAL),  # 70%
        ]

        for i, (degradation, expected_level) in enumerate(test_cases):
            session = analyzer.create_session(
                session_id=f"drift-test-{i}",
                query=f"Test {i}",
            )

            # Calculate what semantic density values would produce the degradation
            semantic_density_before = 1.0
            semantic_density_after = semantic_density_before * (1 - degradation)

            analyzer.record_cycle(
                cycle_number=1,
                compression_ratio=0.5,
                semantic_density_before=semantic_density_before,
                semantic_density_after=semantic_density_after,
            )

            final_session = analyzer.finalize_session()

            assert final_session.max_drift_level == expected_level

    def test_drift_regression_detection(self):
        """Test regression detection."""
        analyzer = SemanticDriftAnalyzer()

        session = analyzer.create_session(
            session_id="regression-test",
            query="Test",
        )

        # Record cycle with 12% degradation
        analyzer.record_cycle(
            cycle_number=1,
            compression_ratio=0.5,
            semantic_density_before=1.0,
            semantic_density_after=0.88,
        )

        analyzer.finalize_session()

        # Check regression with 10% threshold
        is_regression = analyzer.detect_regression(
            session_id="regression-test", threshold_percentage=10.0
        )

        assert is_regression is True

    def test_provider_drift_comparison(self):
        """Test provider drift comparison."""
        analyzer = SemanticDriftAnalyzer()

        providers = ["claude", "openai", "gemini"]

        for provider in providers:
            for i in range(2):
                session = analyzer.create_session(
                    session_id=f"{provider}-{i}",
                    query=f"Query {i}",
                    provider=provider,
                )

                analyzer.record_cycle(
                    cycle_number=1,
                    compression_ratio=0.5,
                    semantic_density_before=1.0,
                    semantic_density_after=0.85 if provider == "openai" else 0.90,
                )

                analyzer.finalize_session()

        comparison = analyzer.get_provider_drift_comparison()

        assert len(comparison) >= 2
        assert all("avg_degradation_percentage" in comparison[p] for p in comparison)

    def test_drift_statistics(self):
        """Test drift statistics calculation."""
        analyzer = SemanticDriftAnalyzer()

        for i in range(3):
            session = analyzer.create_session(
                session_id=f"stat-test-{i}",
                query=f"Query {i}",
            )

            analyzer.record_cycle(
                cycle_number=1,
                compression_ratio=0.5,
                semantic_density_before=1.0,
                semantic_density_after=0.85,
            )

            analyzer.finalize_session()

        stats = analyzer.get_drift_statistics()

        assert stats["total_sessions"] == 3
        assert "drift_distribution" in stats
        assert stats["avg_degradation_percentage"] > 0


class TestTelemetryIntegration:
    """Test integration between telemetry services."""

    def test_complete_pipeline_trace(self):
        """Test tracing a complete pipeline execution."""
        trace_service = RuntimeTraceService()
        token_service = TokenAnalyticsService()
        profiler = LatencyProfiler()

        # Simulate a complete pipeline execution
        trace = trace_service.start_execution(
            query="Complex code analysis",
            query_type="code",
            provider="claude",
            compression_mode="balanced",
            token_budget=8000,
            input_memories_count=10,
        )

        profile = profiler.create_profile(
            profile_id=trace.trace_id,
            provider="claude",
            compression_mode="balanced",
            query_type="code",
        )

        # Retrieval stage
        trace_service.record_stage(
            stage=TraceStage.RETRIEVAL,
            duration_ms=12.5,
            input_token_count=5000,
            output_token_count=4500,
        )
        profiler.record_stage_latency(profile, "retrieval", 12.5, 100, 95)

        # Compression stage
        trace_service.record_stage(
            stage=TraceStage.COMPRESSION,
            duration_ms=45.3,
            input_token_count=4500,
            output_token_count=2000,
            compression_ratio=0.444,
        )
        profiler.record_stage_latency(profile, "compression", 45.3, 95, 50)

        # Generation stage
        trace_service.record_stage(
            stage=TraceStage.GENERATION,
            duration_ms=30.1,
            input_token_count=2000,
            output_token_count=1800,
        )
        profiler.record_stage_latency(profile, "generation", 30.1, 50, 50)

        # Finalize
        final_trace = trace_service.finalize_execution(
            success=True,
            output_context_tokens=1800,
            overall_quality_score=0.94,
        )
        profiler.finalize_profile(profile)

        # Record token metrics
        token_metrics = TokenMetrics(
            query="Complex code analysis",
            query_type="code",
            provider="claude",
            compression_mode="balanced",
            raw_tokens_input=5000,
            compressed_tokens_output=1800,
            token_budget=8000,
            tokens_saved=3200,
            compression_ratio=0.36,
            efficiency_ratio=0.92,
        )
        token_service.record_metrics(token_metrics)

        # Verify all services recorded data
        assert len(trace_service.traces) == 1
        assert len(token_service.metrics) == 1
        assert len(profiler.profiles) == 1
        assert len(token_service.metrics) == 1

        # Verify integration
        assert final_trace.trace_id == profile.profile_id
        assert (
            final_trace.output_context_tokens == token_metrics.compressed_tokens_output
        )


class TestProviderBenchmarkingService:
    """Test provider benchmarking service."""

    def test_record_benchmark(self):
        """Test recording provider benchmarks."""
        service = ProviderBenchmarkingService()

        result = service.record_benchmark(
            benchmark_id="bench-1",
            provider="claude",
            compression_mode="balanced",
            query_complexity=QueryComplexity.MODERATE,
            token_budget=4000,
            raw_tokens=1000,
            compressed_tokens=600,
            semantic_density=0.92,
            reasoning_preservation=0.88,
            entity_preservation=0.90,
            latency_ms=45.5,
            p95_latency_ms=80.2,
            success=True,
        )

        assert result.provider == "claude"
        assert result.overall_score > 0
        assert result.performance_tier in [
            ProviderStrength.EXCELLENT,
            ProviderStrength.STRONG,
            ProviderStrength.MODERATE,
            ProviderStrength.WEAK,
        ]
        assert len(result.strengths) > 0 or len(result.weaknesses) > 0

    def test_compare_providers(self):
        """Test comparing multiple providers."""
        service = ProviderBenchmarkingService()

        providers = ["claude", "openai", "gemini"]
        configurations = [
            {"raw": 1000, "compressed": 600, "density": 0.92, "latency": 45},
            {"raw": 1000, "compressed": 650, "density": 0.85, "latency": 60},
            {"raw": 1000, "compressed": 550, "density": 0.95, "latency": 50},
        ]

        # Record benchmarks
        for i, (provider, config) in enumerate(zip(providers, configurations)):
            service.record_benchmark(
                benchmark_id=f"bench-{i}",
                provider=provider,
                compression_mode="balanced",
                query_complexity=QueryComplexity.MODERATE,
                token_budget=4000,
                raw_tokens=config["raw"],
                compressed_tokens=config["compressed"],
                semantic_density=config["density"],
                reasoning_preservation=0.85,
                entity_preservation=0.88,
                latency_ms=config["latency"],
                p95_latency_ms=config["latency"] * 1.5,
            )

        # Compare
        comparison = service.compare_providers(
            comparison_id="comp-1",
            providers=providers,
            compression_mode="balanced",
            query_complexity=QueryComplexity.MODERATE,
            token_budget=4000,
        )

        assert comparison.recommended_provider in providers
        assert len(comparison.compression_ranking) == 3
        assert len(comparison.latency_ranking) == 3
        assert len(comparison.quality_ranking) == 3
        assert len(comparison.overall_ranking) == 3

    def test_provider_profile(self):
        """Test generating provider profile."""
        service = ProviderBenchmarkingService()

        # Record multiple benchmarks for a provider
        for i in range(3):
            service.record_benchmark(
                benchmark_id=f"bench-{i}",
                provider="claude",
                compression_mode="balanced",
                query_complexity=QueryComplexity.MODERATE,
                token_budget=4000,
                raw_tokens=1000,
                compressed_tokens=600 + (i * 10),
                semantic_density=0.92,
                reasoning_preservation=0.88,
                entity_preservation=0.90,
                latency_ms=45.0 + (i * 5),
                p95_latency_ms=80.0,
            )

        profile = service.get_provider_profile("claude")

        assert profile["provider"] == "claude"
        assert profile["total_benchmarks"] == 3
        assert "by_compression_mode" in profile

    def test_optimization_recommendations(self):
        """Test getting optimization recommendations."""
        service = ProviderBenchmarkingService()

        # Record benchmark with weaknesses
        service.record_benchmark(
            benchmark_id="bench-poor",
            provider="openai",
            compression_mode="aggressive",
            query_complexity=QueryComplexity.COMPLEX,
            token_budget=4000,
            raw_tokens=2000,
            compressed_tokens=1800,  # Poor compression
            semantic_density=0.70,  # Low quality
            reasoning_preservation=0.65,
            entity_preservation=0.68,
            latency_ms=250.0,  # High latency
            p95_latency_ms=400.0,
        )

        recommendations = service.get_optimization_recommendations(
            provider="openai",
            compression_mode="aggressive",
            query_complexity=QueryComplexity.COMPLEX,
        )

        assert "weaknesses" in recommendations
        assert "recommendations" in recommendations
        assert len(recommendations["recommendations"]) > 0

    def test_strength_weakness_analysis(self):
        """Test provider strength/weakness analysis."""
        service = ProviderBenchmarkingService()

        # Record excellent provider
        excellent = service.record_benchmark(
            benchmark_id="bench-excellent",
            provider="claude",
            compression_mode="balanced",
            query_complexity=QueryComplexity.MODERATE,
            token_budget=4000,
            raw_tokens=1000,
            compressed_tokens=400,  # Excellent compression
            semantic_density=0.98,  # Excellent quality
            reasoning_preservation=0.96,
            entity_preservation=0.97,
            latency_ms=25.0,  # Fast
            p95_latency_ms=50.0,
        )

        assert len(excellent.strengths) > 0
        assert "compression" in " ".join(excellent.strengths).lower()

        # Record poor provider
        poor = service.record_benchmark(
            benchmark_id="bench-poor",
            provider="gemini",
            compression_mode="balanced",
            query_complexity=QueryComplexity.MODERATE,
            token_budget=4000,
            raw_tokens=1000,
            compressed_tokens=900,  # Poor compression
            semantic_density=0.60,  # Low quality
            reasoning_preservation=0.50,
            entity_preservation=0.55,
            latency_ms=300.0,  # Slow
            p95_latency_ms=500.0,
        )

        assert len(poor.weaknesses) > 0

    def test_benchmarking_report(self):
        """Test generating benchmarking report."""
        service = ProviderBenchmarkingService()

        # Record some benchmarks
        for provider in ["claude", "openai"]:
            service.record_benchmark(
                benchmark_id=f"bench-{provider}",
                provider=provider,
                compression_mode="balanced",
                query_complexity=QueryComplexity.MODERATE,
                token_budget=4000,
                raw_tokens=1000,
                compressed_tokens=600,
                semantic_density=0.90,
                reasoning_preservation=0.85,
                entity_preservation=0.88,
                latency_ms=50.0,
                p95_latency_ms=100.0,
            )

        report = service.get_benchmarking_report()

        assert "total_benchmarks" in report
        assert "providers" in report
        assert len(report["providers"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
