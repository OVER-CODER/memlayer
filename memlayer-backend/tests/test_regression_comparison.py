"""
Tests for Regression Replay & Comparison Suite.

Tests all components of cross-version trace comparison, semantic regression
detection, and performance improvement validation.
"""

import pytest
from datetime import datetime, timedelta, timezone
from app.runtime.regression_comparison import (
    RegressionDetector,
    CrossVersionComparator,
    RegressionHistoryTracker,
    RegressionEvent,
    CrossVersionComparison,
    ProviderVersionAnalysis,
    RegressionType,
    RegressionSeverity,
)


class TestRegressionDetection:
    """Test suite for RegressionDetector."""

    def test_detector_initialization(self):
        """Test detector initialization."""
        detector = RegressionDetector()
        assert detector.quality_threshold == 0.05
        assert detector.latency_threshold == 0.10
        assert detector.semantic_threshold == 0.08
        assert detector.token_threshold == 0.10
        assert len(detector.detected_regressions) == 0

    def test_quality_degradation_detection(self):
        """Test detection of quality degradation."""
        detector = RegressionDetector(quality_threshold=0.05)

        baseline_trace = {
            "trace_id": "trace_1",
            "quality_score": 0.95,
            "semantic_retention": 0.90,
            "token_efficiency": 0.85,
            "total_duration_ms": 1000,
            "provider": "gpt-4",
            "compression_mode": "balanced",
            "query_type": "reasoning",
            "domain": "research",
            "memories_count": 10,
        }

        comparison_trace = {
            "trace_id": "trace_1_v2",
            "quality_score": 0.85,  # 10% degradation
            "semantic_retention": 0.90,
            "token_efficiency": 0.85,
            "total_duration_ms": 1000,
            "provider": "gpt-4",
            "compression_mode": "balanced",
            "query_type": "reasoning",
            "domain": "research",
            "memories_count": 10,
        }

        regression = detector.detect_regression(
            baseline_trace, comparison_trace, "v1.0", "v2.0", "reg_1"
        )

        assert regression is not None
        assert regression.regression_type == RegressionType.QUALITY_DEGRADATION
        assert regression.quality_delta == -0.10
        assert regression.severity in [
            RegressionSeverity.HIGH,
            RegressionSeverity.CRITICAL,
        ]

    def test_semantic_loss_detection(self):
        """Test detection of semantic loss."""
        detector = RegressionDetector(semantic_threshold=0.08)

        baseline_trace = {
            "trace_id": "trace_2",
            "quality_score": 0.90,
            "semantic_retention": 0.95,
            "token_efficiency": 0.85,
            "total_duration_ms": 1000,
            "provider": "gpt-4",
            "compression_mode": "aggressive",
            "query_type": "retrieval",
            "domain": "software_engineering",
            "memories_count": 20,
        }

        comparison_trace = {
            "trace_id": "trace_2_v2",
            "quality_score": 0.90,
            "semantic_retention": 0.82,  # 13% loss
            "token_efficiency": 0.85,
            "total_duration_ms": 1000,
            "provider": "gpt-4",
            "compression_mode": "aggressive",
            "query_type": "retrieval",
            "domain": "software_engineering",
            "memories_count": 20,
        }

        regression = detector.detect_regression(
            baseline_trace, comparison_trace, "v1.0", "v2.0", "reg_2"
        )

        assert regression is not None
        assert regression.regression_type == RegressionType.SEMANTIC_LOSS
        assert regression.semantic_delta == pytest.approx(-0.13, abs=0.01)

    def test_token_efficiency_regression(self):
        """Test detection of token efficiency regression."""
        detector = RegressionDetector(token_threshold=0.10)

        baseline_trace = {
            "trace_id": "trace_3",
            "quality_score": 0.90,
            "semantic_retention": 0.90,
            "token_efficiency": 0.80,
            "total_duration_ms": 1000,
            "provider": "gpt-3.5",
            "compression_mode": "minimal",
            "query_type": "summary",
            "domain": "documents",
            "memories_count": 50,
        }

        comparison_trace = {
            "trace_id": "trace_3_v2",
            "quality_score": 0.90,
            "semantic_retention": 0.90,
            "token_efficiency": 0.70,  # 12.5% degradation
            "total_duration_ms": 1000,
            "provider": "gpt-3.5",
            "compression_mode": "minimal",
            "query_type": "summary",
            "domain": "documents",
            "memories_count": 50,
        }

        regression = detector.detect_regression(
            baseline_trace, comparison_trace, "v1.0", "v2.0", "reg_3"
        )

        assert regression is not None
        assert regression.regression_type == RegressionType.COMPRESSION_INEFFICIENCY

    def test_no_regression_on_improvement(self):
        """Test that improvements are not flagged as regressions."""
        detector = RegressionDetector()

        baseline_trace = {
            "trace_id": "trace_4",
            "quality_score": 0.85,
            "semantic_retention": 0.85,
            "token_efficiency": 0.75,
            "total_duration_ms": 1000,
            "provider": "gpt-4",
            "compression_mode": "balanced",
            "query_type": "reasoning",
            "domain": "research",
            "memories_count": 10,
        }

        comparison_trace = {
            "trace_id": "trace_4_v2",
            "quality_score": 0.95,  # 10% improvement
            "semantic_retention": 0.95,  # 10% improvement
            "token_efficiency": 0.85,  # 10% improvement
            "total_duration_ms": 800,  # 20% latency improvement
            "provider": "gpt-4",
            "compression_mode": "balanced",
            "query_type": "reasoning",
            "domain": "research",
            "memories_count": 10,
        }

        regression = detector.detect_regression(
            baseline_trace, comparison_trace, "v1.0", "v2.0", "reg_4"
        )

        assert regression is None

    def test_severity_calculation_critical(self):
        """Test critical severity detection."""
        detector = RegressionDetector()

        baseline_trace = {
            "trace_id": "trace_5",
            "quality_score": 0.90,
            "semantic_retention": 0.90,
            "token_efficiency": 0.85,
            "total_duration_ms": 1000,
            "provider": "gpt-4",
            "compression_mode": "balanced",
            "query_type": "reasoning",
            "domain": "research",
            "memories_count": 10,
        }

        comparison_trace = {
            "trace_id": "trace_5_v2",
            "quality_score": 0.50,  # 40% degradation
            "semantic_retention": 0.60,  # 30% loss
            "token_efficiency": 0.65,  # 24% degradation
            "total_duration_ms": 1500,
            "provider": "gpt-4",
            "compression_mode": "balanced",
            "query_type": "reasoning",
            "domain": "research",
            "memories_count": 10,
        }

        regression = detector.detect_regression(
            baseline_trace, comparison_trace, "v1.0", "v2.0", "reg_5"
        )

        assert regression is not None
        assert regression.severity == RegressionSeverity.CRITICAL

    def test_root_cause_identification(self):
        """Test identification of root causes."""
        detector = RegressionDetector()

        baseline_trace = {
            "trace_id": "trace_6",
            "quality_score": 0.90,
            "semantic_retention": 0.90,
            "token_efficiency": 0.85,
            "total_duration_ms": 1000,
            "provider": "gpt-4",
            "compression_mode": "balanced",
            "query_type": "reasoning",
            "domain": "research",
            "memories_count": 10,
            "token_metrics": {"total_tokens": 5000},
        }

        comparison_trace = {
            "trace_id": "trace_6_v2",
            "quality_score": 0.80,
            "semantic_retention": 0.85,
            "token_efficiency": 0.75,
            "total_duration_ms": 1200,
            "provider": "gpt-4",
            "compression_mode": "aggressive",  # changed
            "query_type": "reasoning",
            "domain": "research",
            "memories_count": 30,  # increased
            "token_metrics": {"total_tokens": 6500},  # increased
        }

        regression = detector.detect_regression(
            baseline_trace, comparison_trace, "v1.0", "v2.0", "reg_6"
        )

        assert regression is not None
        assert "compression_mode_change" in regression.root_cause_indicators
        assert "memory_bloat" in regression.root_cause_indicators

    def test_impact_estimation(self):
        """Test impact estimation."""
        detector = RegressionDetector()

        baseline_trace = {
            "trace_id": "trace_7",
            "quality_score": 0.90,
            "semantic_retention": 0.90,
            "token_efficiency": 0.85,
            "total_duration_ms": 1000,
            "provider": "gpt-4",
            "compression_mode": "balanced",
            "query_type": "reasoning",
            "domain": "research",
            "memories_count": 10,
        }

        comparison_trace = {
            "trace_id": "trace_7_v2",
            "quality_score": 0.75,  # 15% loss
            "semantic_retention": 0.80,  # 10% loss
            "token_efficiency": 0.70,  # 18% loss
            "total_duration_ms": 1200,
            "provider": "gpt-4",
            "compression_mode": "balanced",
            "query_type": "reasoning",
            "domain": "research",
            "memories_count": 10,
        }

        regression = detector.detect_regression(
            baseline_trace, comparison_trace, "v1.0", "v2.0", "reg_7"
        )

        assert regression is not None
        assert regression.estimated_impact > 0
        assert regression.user_visible is True


class TestCrossVersionComparison:
    """Test suite for CrossVersionComparator."""

    def test_comparator_initialization(self):
        """Test comparator initialization."""
        comparator = CrossVersionComparator()
        assert comparator.regression_detector is not None
        assert len(comparator.comparisons) == 0

    def test_trace_matching(self):
        """Test trace matching between versions."""
        comparator = CrossVersionComparator()

        baseline_traces = [
            {
                "trace_id": "b1",
                "query": "What is ML?",
                "provider": "gpt-4",
                "compression_mode": "balanced",
                "quality_score": 0.90,
                "semantic_retention": 0.90,
                "token_efficiency": 0.85,
                "total_duration_ms": 1000,
                "memories_count": 10,
            },
            {
                "trace_id": "b2",
                "query": "Explain ML",
                "provider": "gpt-4",
                "compression_mode": "balanced",
                "quality_score": 0.85,
                "semantic_retention": 0.85,
                "token_efficiency": 0.80,
                "total_duration_ms": 1500,
                "memories_count": 15,
            },
        ]

        comparison_traces = [
            {
                "trace_id": "c1",
                "query": "What is ML?",
                "provider": "gpt-4",
                "compression_mode": "balanced",
                "quality_score": 0.92,
                "semantic_retention": 0.92,
                "token_efficiency": 0.88,
                "total_duration_ms": 950,
                "memories_count": 11,
            },
            {
                "trace_id": "c2",
                "query": "Explain ML",
                "provider": "gpt-4",
                "compression_mode": "balanced",
                "quality_score": 0.88,
                "semantic_retention": 0.88,
                "token_efficiency": 0.83,
                "total_duration_ms": 1400,
                "memories_count": 16,
            },
        ]

        comparison = comparator.compare_versions(
            baseline_traces, comparison_traces, "v1.0", "v2.0", "cmp_1"
        )

        assert comparison.baseline_traces == 2
        assert comparison.comparison_traces == 2
        assert comparison.comparable_traces == 2

    def test_version_comparison_with_regressions(self):
        """Test version comparison detecting regressions."""
        comparator = CrossVersionComparator()

        baseline_traces = [
            {
                "trace_id": "b1",
                "query": "Q1",
                "provider": "gpt-4",
                "compression_mode": "balanced",
                "quality_score": 0.90,
                "semantic_retention": 0.90,
                "token_efficiency": 0.85,
                "total_duration_ms": 1000,
                "memories_count": 10,
                "domain": "research",
            },
        ]

        comparison_traces = [
            {
                "trace_id": "c1",
                "query": "Q1",
                "provider": "gpt-4",
                "compression_mode": "balanced",
                "quality_score": 0.75,  # 15% regression
                "semantic_retention": 0.80,
                "token_efficiency": 0.75,
                "total_duration_ms": 1500,
                "memories_count": 10,
                "domain": "research",
            },
        ]

        comparison = comparator.compare_versions(
            baseline_traces, comparison_traces, "v1.0", "v2.0", "cmp_2"
        )

        assert comparison.is_regression_overall is True
        assert comparison.total_regressions >= 1

    def test_provider_regression_tracking(self):
        """Test tracking of regressions by provider."""
        comparator = CrossVersionComparator()

        baseline_traces = [
            {
                "trace_id": "b1",
                "query": "Q1",
                "provider": "gpt-4",
                "compression_mode": "balanced",
                "quality_score": 0.90,
                "semantic_retention": 0.90,
                "token_efficiency": 0.85,
                "total_duration_ms": 1000,
                "memories_count": 10,
            },
            {
                "trace_id": "b2",
                "query": "Q2",
                "provider": "claude",
                "compression_mode": "balanced",
                "quality_score": 0.88,
                "semantic_retention": 0.88,
                "token_efficiency": 0.83,
                "total_duration_ms": 1200,
                "memories_count": 12,
            },
        ]

        comparison_traces = [
            {
                "trace_id": "c1",
                "query": "Q1",
                "provider": "gpt-4",
                "compression_mode": "balanced",
                "quality_score": 0.70,  # regression
                "semantic_retention": 0.75,
                "token_efficiency": 0.65,
                "total_duration_ms": 1500,
                "memories_count": 10,
            },
            {
                "trace_id": "c2",
                "query": "Q2",
                "provider": "claude",
                "compression_mode": "balanced",
                "quality_score": 0.87,  # stable/slight improvement
                "semantic_retention": 0.88,
                "token_efficiency": 0.84,
                "total_duration_ms": 1100,
                "memories_count": 12,
            },
        ]

        comparison = comparator.compare_versions(
            baseline_traces, comparison_traces, "v1.0", "v2.0", "cmp_3"
        )

        assert (
            "gpt-4" in comparison.provider_regressions
            or comparison.total_regressions > 0
        )

    def test_verdict_generation_regression(self):
        """Test verdict generation for regression case."""
        comparator = CrossVersionComparator()

        baseline_traces = [
            {
                "trace_id": f"b{i}",
                "query": f"Q{i}",
                "provider": "gpt-4",
                "compression_mode": "balanced",
                "quality_score": 0.90,
                "semantic_retention": 0.90,
                "token_efficiency": 0.85,
                "total_duration_ms": 1000,
                "memories_count": 10,
            }
            for i in range(10)
        ]

        comparison_traces = [
            {
                "trace_id": f"c{i}",
                "query": f"Q{i}",
                "provider": "gpt-4",
                "compression_mode": "balanced",
                "quality_score": 0.70,  # All regressing
                "semantic_retention": 0.75,
                "token_efficiency": 0.65,
                "total_duration_ms": 1500,
                "memories_count": 10,
            }
            for i in range(10)
        ]

        comparison = comparator.compare_versions(
            baseline_traces, comparison_traces, "v1.0", "v2.0", "cmp_4"
        )

        assert comparison.is_regression_overall is True
        assert (
            "REJECT" in comparison.recommendation
            or "CAUTION" in comparison.recommendation
        )

    def test_verdict_generation_improvement(self):
        """Test verdict generation for improvement case."""
        comparator = CrossVersionComparator()

        baseline_traces = [
            {
                "trace_id": f"b{i}",
                "query": f"Q{i}",
                "provider": "gpt-4",
                "compression_mode": "balanced",
                "quality_score": 0.80,
                "semantic_retention": 0.80,
                "token_efficiency": 0.75,
                "total_duration_ms": 1500,
                "memories_count": 10,
            }
            for i in range(10)
        ]

        comparison_traces = [
            {
                "trace_id": f"c{i}",
                "query": f"Q{i}",
                "provider": "gpt-4",
                "compression_mode": "balanced",
                "quality_score": 0.95,  # All improving
                "semantic_retention": 0.95,
                "token_efficiency": 0.90,
                "total_duration_ms": 800,
                "memories_count": 10,
            }
            for i in range(10)
        ]

        comparison = comparator.compare_versions(
            baseline_traces, comparison_traces, "v1.0", "v2.0", "cmp_5"
        )

        assert comparison.is_regression_overall is False
        assert (
            "APPROVED" in comparison.recommendation
            or "NEUTRAL" in comparison.recommendation
        )


class TestRegressionHistoryTracker:
    """Test suite for RegressionHistoryTracker."""

    def test_tracker_initialization(self):
        """Test tracker initialization."""
        tracker = RegressionHistoryTracker()
        assert len(tracker.regression_history) == 0
        assert len(tracker.comparison_history) == 0
        assert len(tracker.version_timeline) == 0

    def test_record_regression(self):
        """Test recording regression events."""
        tracker = RegressionHistoryTracker()

        event = RegressionEvent(
            event_id="evt_1",
            timestamp=datetime.now(timezone.utc),
            baseline_trace_id="b1",
            comparison_trace_id="c1",
            baseline_version="v1.0",
            comparison_version="v2.0",
            regression_type=RegressionType.QUALITY_DEGRADATION,
            severity=RegressionSeverity.HIGH,
            quality_delta=-0.15,
            provider="gpt-4",
        )

        tracker.record_regression(event)

        assert len(tracker.regression_history) == 1
        assert "v2.0" in tracker.version_timeline

    def test_get_regression_trends(self):
        """Test getting regression trends."""
        tracker = RegressionHistoryTracker()

        for i in range(5):
            event = RegressionEvent(
                event_id=f"evt_{i}",
                timestamp=datetime.now(timezone.utc),
                baseline_trace_id=f"b{i}",
                comparison_trace_id=f"c{i}",
                baseline_version="v1.0",
                comparison_version="v2.0",
                regression_type=RegressionType.QUALITY_DEGRADATION,
                severity=RegressionSeverity.HIGH if i < 3 else RegressionSeverity.LOW,
                quality_delta=-0.10,
                provider="gpt-4",
            )
            tracker.record_regression(event)

        trends = tracker.get_regression_trends()

        assert trends["total_regressions"] == 5
        assert "QUALITY_DEGRADATION" in trends["by_type"]
        assert trends["by_type"]["quality_degradation"] == 5

    def test_get_provider_regression_summary(self):
        """Test provider regression summary."""
        tracker = RegressionHistoryTracker()

        providers = ["gpt-4", "gpt-4", "claude", "gpt-3.5"]
        for i, provider in enumerate(providers):
            event = RegressionEvent(
                event_id=f"evt_{i}",
                timestamp=datetime.now(timezone.utc),
                baseline_trace_id=f"b{i}",
                comparison_trace_id=f"c{i}",
                baseline_version="v1.0",
                comparison_version="v2.0",
                regression_type=RegressionType.QUALITY_DEGRADATION,
                severity=RegressionSeverity.MEDIUM,
                quality_delta=-0.08,
                provider=provider,
            )
            tracker.record_regression(event)

        summary = tracker.get_provider_regression_summary()

        assert summary["gpt-4"] == 2
        assert summary["claude"] == 1
        assert summary["gpt-3.5"] == 1

    def test_get_critical_regressions(self):
        """Test retrieving critical regressions."""
        tracker = RegressionHistoryTracker()

        # Add mixed severity events
        severities = [
            RegressionSeverity.CRITICAL,
            RegressionSeverity.HIGH,
            RegressionSeverity.CRITICAL,
            RegressionSeverity.LOW,
        ]
        for i, severity in enumerate(severities):
            event = RegressionEvent(
                event_id=f"evt_{i}",
                timestamp=datetime.now(timezone.utc),
                baseline_trace_id=f"b{i}",
                comparison_trace_id=f"c{i}",
                baseline_version="v1.0",
                comparison_version="v2.0",
                regression_type=RegressionType.QUALITY_DEGRADATION,
                severity=severity,
                quality_delta=-0.20
                if severity == RegressionSeverity.CRITICAL
                else -0.08,
                provider="gpt-4",
            )
            tracker.record_regression(event)

        critical = tracker.get_critical_regressions()

        assert len(critical) == 2
        assert all(e.severity == RegressionSeverity.CRITICAL for e in critical)


class TestRegressionComparison:
    """Integration tests for regression comparison across versions."""

    def test_end_to_end_version_comparison(self):
        """Test complete version comparison workflow."""
        detector = RegressionDetector()
        comparator = CrossVersionComparator(detector)
        tracker = RegressionHistoryTracker()

        # Create realistic baseline traces
        baseline_traces = [
            {
                "trace_id": f"baseline_{i}",
                "query": f"Query {i}",
                "provider": ["gpt-4", "gpt-4", "claude"][i % 3],
                "compression_mode": ["balanced", "aggressive"][i % 2],
                "quality_score": 0.88 + (i * 0.01),
                "semantic_retention": 0.87 + (i * 0.01),
                "token_efficiency": 0.82 + (i * 0.01),
                "total_duration_ms": 1000 + (i * 50),
                "memories_count": 10 + (i * 2),
                "query_type": ["reasoning", "retrieval", "summary"][i % 3],
                "domain": ["research", "software_engineering", "documents"][i % 3],
            }
            for i in range(15)
        ]

        # Create comparison traces with controlled degradation
        comparison_traces = [
            {
                "trace_id": f"v2_{i}",
                "query": f"Query {i}",
                "provider": ["gpt-4", "gpt-4", "claude"][i % 3],
                "compression_mode": ["balanced", "aggressive"][i % 2],
                "quality_score": (0.88 + (i * 0.01))
                - (0.05 if i < 8 else 0),  # 8 regressions
                "semantic_retention": (0.87 + (i * 0.01)) - (0.04 if i < 8 else 0),
                "token_efficiency": (0.82 + (i * 0.01)) - (0.06 if i < 8 else 0),
                "total_duration_ms": (1000 + (i * 50)) + (150 if i < 8 else 0),
                "memories_count": 10 + (i * 2),
                "query_type": ["reasoning", "retrieval", "summary"][i % 3],
                "domain": ["research", "software_engineering", "documents"][i % 3],
            }
            for i in range(15)
        ]

        # Run comparison
        comparison = comparator.compare_versions(
            baseline_traces, comparison_traces, "v1.0", "v2.0", "full_cmp"
        )

        # Record all regressions
        for regression in detector.detected_regressions:
            tracker.record_regression(regression)
        tracker.record_comparison(comparison)

        # Validate results
        assert comparison.comparable_traces == 15
        assert comparison.total_regressions >= 8
        assert comparison.is_regression_overall is True
        assert len(tracker.regression_history) >= 8

        # Validate provider tracking
        assert (
            "gpt-4" in comparison.provider_regressions
            or len(comparison.provider_regressions) > 0
        )

    def test_multiple_version_comparison_chain(self):
        """Test comparing across multiple version chains."""
        tracker = RegressionHistoryTracker()

        # Simulate version progression
        versions = ["v1.0", "v1.1", "v2.0", "v2.1"]

        for i in range(len(versions) - 1):
            comparison = CrossVersionComparison(
                comparison_id=f"cmp_{i}",
                timestamp=datetime.now(timezone.utc) - timedelta(hours=len(versions) - i - 1),
                baseline_version=versions[i],
                comparison_version=versions[i + 1],
                baseline_traces=100,
                comparison_traces=100,
                comparable_traces=100,
                average_quality_delta=-0.02 * (i + 1),
                total_regressions=5 * (i + 1),
                total_improvements=10 - (2 * i),
            )
            tracker.record_comparison(comparison)

        progression = tracker.get_version_progression()

        assert progression["total_comparisons"] == 3
        assert len(progression["versions"]) > 0
        assert progression["progression"][0]["from"] == "v1.0"
        assert progression["progression"][-1]["to"] == "v2.1"
