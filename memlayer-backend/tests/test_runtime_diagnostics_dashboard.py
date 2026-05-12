"""
Tests for Runtime Diagnostics Dashboard.
"""

from datetime import datetime
from unittest.mock import Mock

from app.runtime import RuntimeDiagnosticsDashboard
from app.runtime.failure_detector import EmergentFailureDetector
from app.runtime.replay_engine import RuntimeReplayEngine, ReplayableTrace
from app.runtime.evolution_tracker import RuntimeEvolutionTracker, EvolutionMetric
from app.telemetry import (
    RuntimeTraceService,
    TraceStage,
    TokenAnalyticsService,
    TokenMetrics,
    LatencyProfiler,
    SemanticDriftAnalyzer,
    ProviderBenchmarkingService,
    QueryComplexity,
)


def test_capture_snapshot_and_render_console():
    # Build local telemetry/runtime services with deterministic data.
    trace_service = RuntimeTraceService()
    trace_service.start_execution(
        query="diagnostics query",
        query_type="general",
        provider="claude",
        compression_mode="balanced",
        token_budget=4000,
        input_memories_count=4,
    )
    trace_service.record_stage(
        stage=TraceStage.RANKING,
        duration_ms=15.0,
        input_token_count=200,
        output_token_count=120,
    )
    trace_service.finalize_execution(
        success=True,
        output_context_tokens=120,
        overall_quality_score=0.9,
        semantic_retention=0.88,
    )

    token_analytics = TokenAnalyticsService()
    token_analytics.record_metrics(
        TokenMetrics(
            query="diagnostics query",
            query_type="general",
            provider="claude",
            compression_mode="balanced",
            raw_tokens_input=200,
            compressed_tokens_output=120,
            token_budget=4000,
            tokens_saved=80,
            compression_ratio=0.6,
            efficiency_ratio=0.85,
            semantic_density=0.9,
            entity_preservation=0.9,
            reasoning_continuity=0.88,
            memory_count=4,
            chunk_count=2,
        )
    )

    latency_profiler = LatencyProfiler()
    profile = latency_profiler.create_profile(
        profile_id="profile-1",
        provider="claude",
        compression_mode="balanced",
        query_type="general",
        input_memories_count=4,
    )
    latency_profiler.record_stage_latency(
        profile=profile,
        stage_name="ranking",
        duration_ms=15.0,
        input_size_items=4,
        output_size_items=2,
    )
    latency_profiler.finalize_profile(profile)

    drift_analyzer = SemanticDriftAnalyzer()
    drift_analyzer.create_session(
        session_id="drift-1",
        query="diagnostics query",
        query_type="general",
        provider="claude",
    )
    drift_analyzer.record_cycle(
        cycle_number=1,
        compression_ratio=0.6,
        semantic_density_before=1.0,
        semantic_density_after=0.9,
        topic_preservation=0.9,
        reasoning_preservation=0.88,
        detail_preservation=0.86,
    )
    drift_analyzer.finalize_session()

    benchmarking = ProviderBenchmarkingService()
    benchmarking.record_benchmark(
        benchmark_id="bench-1",
        provider="claude",
        compression_mode="balanced",
        query_complexity=QueryComplexity.MODERATE,
        token_budget=4000,
        raw_tokens=200,
        compressed_tokens=120,
        semantic_density=0.9,
        reasoning_preservation=0.88,
        entity_preservation=0.9,
        latency_ms=60.0,
        p95_latency_ms=80.0,
    )

    replay_engine = RuntimeReplayEngine()
    replay_engine.store_trace(
        ReplayableTrace(
            trace_id="trace-1",
            timestamp=datetime.utcnow(),
            query="diagnostics query",
            query_type="general",
            provider="claude",
            compression_mode="balanced",
            token_budget=4000,
            memories_count=4,
            quality_score=0.9,
            semantic_retention=0.88,
            token_efficiency=0.85,
            total_duration_ms=60.0,
        )
    )
    replay_engine.simulate_replay("trace-1", perturbation_factor=0.0)

    failure_detector = EmergentFailureDetector()
    failure_detector.detect_semantic_collapse(
        failure_id="failure-1",
        query="diagnostics query",
        provider="claude",
        compression_mode="balanced",
        current_semantic_density=0.6,
        previous_semantic_density=1.0,
        cycle_number=1,
    )

    evolution_tracker = RuntimeEvolutionTracker()
    evolution_tracker.record_datapoint(
        metric=EvolutionMetric.CONTEXT_QUALITY,
        value=0.9,
        provider="claude",
    )

    runtime = Mock()
    runtime.get_runtime_statistics.return_value = {
        "total_executions": 1,
        "success_rate": 1.0,
        "avg_quality_score": 0.9,
        "avg_semantic_retention": 0.88,
        "avg_token_efficiency": 0.85,
        "avg_duration_ms": 60.0,
    }

    dashboard = RuntimeDiagnosticsDashboard(
        integrated_runtime=runtime,
        trace_service=trace_service,
        token_analytics=token_analytics,
        latency_profiler=latency_profiler,
        drift_analyzer=drift_analyzer,
        benchmarking_service=benchmarking,
        replay_engine=replay_engine,
        failure_detector=failure_detector,
        evolution_tracker=evolution_tracker,
    )

    snapshot = dashboard.capture_snapshot(snapshot_id="diag-1")
    console = dashboard.render_console_report(snapshot)

    assert snapshot.snapshot_id == "diag-1"
    assert snapshot.runtime_overview["total_executions"] == 1
    assert snapshot.replay_diagnostics["stored_traces"] == 1
    assert snapshot.failure_propagation["total_failures"] >= 1
    assert len(snapshot.context_evolution_timeline) == 1
    assert "MEMLAYER RUNTIME DIAGNOSTICS CONSOLE" in console
