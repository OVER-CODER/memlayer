"""
Additional tests for regression comparison extensions.
"""

from datetime import datetime

from app.runtime.regression_comparison import (
    CrossVersionComparator,
    RegressionHistoryTracker,
    RegressionEvent,
    RegressionType,
    RegressionSeverity,
    CrossVersionComparison,
)


def test_provider_version_analysis_generation():
    comparator = CrossVersionComparator()
    baseline = [
        {
            "trace_id": "b1",
            "query": "q1",
            "provider": "claude",
            "compression_mode": "balanced",
            "quality_score": 0.9,
            "semantic_retention": 0.9,
            "token_efficiency": 0.85,
            "total_duration_ms": 1000,
            "memories_count": 10,
        },
    ]
    comparison = [
        {
            "trace_id": "c1",
            "query": "q1",
            "provider": "claude",
            "compression_mode": "balanced",
            "quality_score": 0.8,
            "semantic_retention": 0.82,
            "token_efficiency": 0.75,
            "total_duration_ms": 1200,
            "memories_count": 10,
        },
    ]

    comparator.compare_versions(
        baseline_traces=baseline,
        comparison_traces=comparison,
        baseline_version="v1",
        comparison_version="v2",
        comparison_id="cmp-ext",
    )
    analyses = comparator.analyze_provider_versions(
        baseline_traces=baseline,
        comparison_traces=comparison,
        baseline_version="v1",
        comparison_version="v2",
    )

    assert len(analyses) == 1
    assert analyses[0].provider == "claude"
    assert analyses[0].quality_delta < 0
    assert analyses[0].status_change == "degraded"


def test_history_export_and_load(tmp_path):
    tracker = RegressionHistoryTracker()
    event = RegressionEvent(
        event_id="evt-1",
        timestamp=datetime.utcnow(),
        baseline_trace_id="b1",
        comparison_trace_id="c1",
        baseline_version="v1",
        comparison_version="v2",
        regression_type=RegressionType.QUALITY_DEGRADATION,
        severity=RegressionSeverity.HIGH,
        quality_delta=-0.1,
        provider="claude",
    )
    tracker.record_regression(event)
    tracker.record_comparison(
        CrossVersionComparison(
            comparison_id="cmp-1",
            timestamp=datetime.utcnow(),
            baseline_version="v1",
            comparison_version="v2",
            comparable_traces=1,
            total_regressions=1,
        )
    )

    output = tmp_path / "history.json"
    tracker.export_history(str(output))

    restored = RegressionHistoryTracker()
    restored.load_history(str(output))

    assert len(restored.regression_history) == 1
    assert len(restored.comparison_history) == 1
    trends = restored.get_regression_trends()
    assert "QUALITY_DEGRADATION" in trends["by_type"]
    assert "quality_degradation" in trends["by_type"]
