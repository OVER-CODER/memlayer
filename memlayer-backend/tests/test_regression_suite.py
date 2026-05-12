"""
Tests for Regression Replay Suite orchestration.
"""

from datetime import datetime

from app.runtime import (
    RegressionReplaySuite,
    RuntimeReplayEngine,
    ReplayableTrace,
)


def _trace(
    trace_id: str,
    query: str,
    provider: str,
    quality: float,
    semantic: float,
    efficiency: float,
    latency_ms: float,
):
    return {
        "trace_id": trace_id,
        "query": query,
        "query_type": "general",
        "provider": provider,
        "compression_mode": "balanced",
        "token_budget": 4000,
        "memories_count": 10,
        "quality_score": quality,
        "semantic_retention": semantic,
        "token_efficiency": efficiency,
        "total_duration_ms": latency_ms,
        "domain": "research",
    }


def test_register_and_compare_versions():
    suite = RegressionReplaySuite()

    baseline = [
        _trace("b1", "query-1", "gpt-4", 0.90, 0.91, 0.85, 1000),
        _trace("b2", "query-2", "claude", 0.88, 0.89, 0.83, 950),
    ]
    comparison = [
        _trace("c1", "query-1", "gpt-4", 0.80, 0.79, 0.74, 1200),
        _trace("c2", "query-2", "claude", 0.90, 0.92, 0.87, 900),
    ]

    baseline_set = suite.register_version_traces("v1.0", baseline)
    comparison_set = suite.register_version_traces("v1.1", comparison)

    assert baseline_set.checksum
    assert comparison_set.checksum
    assert baseline_set.checksum != comparison_set.checksum

    report = suite.compare_versions("v1.0", "v1.1", report_id="cmp-v1-v11")

    assert report.report_id == "cmp-v1-v11"
    assert report.comparison is not None
    assert report.comparison.comparable_traces == 2
    assert report.replay_delta_summary["matched_traces"] == 2
    assert "overall_status" in report.optimization_summary


def test_register_from_replay_engine():
    replay_engine = RuntimeReplayEngine()
    replay_engine.store_trace(
        ReplayableTrace(
            trace_id="trace-1",
            timestamp=datetime.utcnow(),
            query="q1",
            query_type="general",
            provider="claude",
            compression_mode="balanced",
            token_budget=4000,
            memories_count=5,
            quality_score=0.9,
            semantic_retention=0.88,
            token_efficiency=0.84,
            total_duration_ms=123.0,
        )
    )
    replay_engine.store_trace(
        ReplayableTrace(
            trace_id="trace-2",
            timestamp=datetime.utcnow(),
            query="q2",
            query_type="general",
            provider="claude",
            compression_mode="balanced",
            token_budget=4000,
            memories_count=6,
            quality_score=0.91,
            semantic_retention=0.89,
            token_efficiency=0.85,
            total_duration_ms=118.0,
        )
    )

    suite = RegressionReplaySuite(replay_engine=replay_engine)
    trace_set = suite.register_version_from_replay_engine(version="v-replay")

    assert trace_set.version == "v-replay"
    assert len(trace_set.traces) == 2
    assert trace_set.checksum
