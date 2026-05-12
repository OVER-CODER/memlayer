"""
Tests for Runtime Evolution Tracker.

Tests for longitudinal tracking of semantic degradation, context quality,
token efficiency, and provider adaptation over time.
"""

import pytest
from datetime import datetime, timedelta
from app.runtime import (
    RuntimeEvolutionTracker,
    EvolutionDataPoint,
    EvolutionTrend,
    EvolutionPeriod,
    EvolutionMetric,
    get_evolution_tracker,
)


class TestEvolutionDataPoint:
    """Test evolution data points."""

    def test_datapoint_creation(self):
        """Test creating evolution data point."""
        datapoint = EvolutionDataPoint(
            timestamp=datetime.utcnow(),
            metric=EvolutionMetric.CONTEXT_QUALITY,
            value=0.85,
            domain="research",
            provider="claude",
        )

        assert datapoint.metric == EvolutionMetric.CONTEXT_QUALITY
        assert datapoint.value == 0.85
        assert datapoint.domain == "research"

    def test_datapoint_to_dict(self):
        """Test converting data point to dict."""
        ts = datetime.utcnow()
        datapoint = EvolutionDataPoint(
            timestamp=ts,
            metric=EvolutionMetric.TOKEN_EFFICIENCY,
            value=0.75,
            context={"complexity": "high"},
        )

        dp_dict = datapoint.to_dict()

        assert dp_dict["metric"] == "token_efficiency"
        assert dp_dict["value"] == 0.75
        assert "complexity" in dp_dict["context"]


class TestEvolutionTrend:
    """Test evolution trend analysis."""

    def test_trend_creation(self):
        """Test creating evolution trend."""
        trend = EvolutionTrend(metric=EvolutionMetric.SEMANTIC_RETENTION)

        assert trend.metric == EvolutionMetric.SEMANTIC_RETENTION
        assert trend.start_value == 0.0
        assert len(trend.data_points) == 0

    def test_trend_to_dict(self):
        """Test converting trend to dict."""
        trend = EvolutionTrend(
            metric=EvolutionMetric.COMPRESSION_RATIO,
            start_value=0.9,
            end_value=0.75,
            avg_value=0.82,
            degradation_rate=-0.05,
        )

        trend_dict = trend.to_dict()

        assert trend_dict["metric"] == "compression_ratio"
        assert trend_dict["start_value"] == 0.9
        assert trend_dict["end_value"] == 0.75


class TestEvolutionPeriod:
    """Test evolution period analysis."""

    def test_period_creation(self):
        """Test creating evolution period."""
        start = datetime.utcnow()
        end = start + timedelta(hours=1)

        period = EvolutionPeriod(
            period_id="period-001",
            start_time=start,
            end_time=end,
            duration_hours=1.0,
        )

        assert period.period_id == "period-001"
        assert period.duration_hours == 1.0
        assert period.overall_stability == 0.0

    def test_period_to_dict(self):
        """Test converting period to dict."""
        start = datetime.utcnow()
        end = start + timedelta(hours=2)

        period = EvolutionPeriod(
            period_id="period-002",
            start_time=start,
            end_time=end,
            duration_hours=2.0,
            overall_stability=85.0,
            critical_degradation_detected=False,
        )

        period_dict = period.to_dict()

        assert period_dict["period_id"] == "period-002"
        assert period_dict["duration_hours"] == 2.0
        assert period_dict["overall_stability"] == 85.0


class TestRuntimeEvolutionTracker:
    """Test runtime evolution tracker."""

    def test_tracker_initialization(self):
        """Test initializing evolution tracker."""
        tracker = RuntimeEvolutionTracker(tracking_window_hours=24)

        assert tracker.tracking_window_hours == 24
        assert len(tracker.all_data_points) == 0
        assert len(tracker.completed_periods) == 0

    def test_record_datapoint(self):
        """Test recording data points."""
        tracker = RuntimeEvolutionTracker()

        dp = tracker.record_datapoint(
            metric=EvolutionMetric.CONTEXT_QUALITY,
            value=0.85,
            domain="research",
            provider="claude",
        )

        assert len(tracker.all_data_points) == 1
        assert dp.value == 0.85
        assert dp.domain == "research"

    def test_record_multiple_datapoints(self):
        """Test recording multiple data points."""
        tracker = RuntimeEvolutionTracker()

        for i in range(10):
            tracker.record_datapoint(
                metric=EvolutionMetric.TOKEN_EFFICIENCY,
                value=0.9 - (i * 0.01),
            )

        assert len(tracker.all_data_points) == 10

    def test_get_current_trend(self):
        """Test getting current trend."""
        tracker = RuntimeEvolutionTracker()

        # Record degrading values
        for i in range(5):
            tracker.record_datapoint(
                metric=EvolutionMetric.CONTEXT_QUALITY,
                value=1.0 - (i * 0.05),
            )

        trend = tracker.get_current_trend(EvolutionMetric.CONTEXT_QUALITY)

        assert trend.metric == EvolutionMetric.CONTEXT_QUALITY
        assert len(trend.data_points) == 5
        assert trend.start_value > trend.end_value  # Degradation

    def test_trend_statistics(self):
        """Test trend statistics calculation."""
        tracker = RuntimeEvolutionTracker()

        values = [0.9, 0.85, 0.80, 0.75, 0.70]
        for v in values:
            tracker.record_datapoint(
                metric=EvolutionMetric.SEMANTIC_RETENTION,
                value=v,
            )

        trend = tracker.get_current_trend(EvolutionMetric.SEMANTIC_RETENTION)

        assert trend.start_value == 0.9
        assert trend.end_value == 0.70
        assert trend.min_value == 0.70
        assert trend.max_value == 0.9
        assert trend.avg_value == 0.8

    def test_degradation_calculation(self):
        """Test degradation rate calculation."""
        tracker = RuntimeEvolutionTracker()

        # Record with timestamps
        base_time = datetime.utcnow()
        for i in range(3):
            # Manually set timestamps 1 hour apart
            dp = EvolutionDataPoint(
                timestamp=base_time + timedelta(hours=i),
                metric=EvolutionMetric.COMPRESSION_RATIO,
                value=1.0 - (i * 0.1),
            )
            tracker.all_data_points.append(dp)

        trend = tracker.get_current_trend(EvolutionMetric.COMPRESSION_RATIO)

        assert trend.degradation_rate < 0  # Should be negative (degrading)
        assert trend.total_degradation > 0

    def test_degradation_type_classification(self):
        """Test degradation type classification."""
        tracker = RuntimeEvolutionTracker()

        # Test stable values
        for _ in range(5):
            tracker.record_datapoint(
                metric=EvolutionMetric.ENTITY_PRESERVATION,
                value=0.85,
            )

        trend = tracker.get_current_trend(EvolutionMetric.ENTITY_PRESERVATION)
        assert trend.degradation_type == "stable"

    def test_volatility_calculation(self):
        """Test volatility calculation."""
        tracker = RuntimeEvolutionTracker()

        # Record volatile values
        values = [0.5, 0.9, 0.4, 0.95, 0.3]
        for v in values:
            tracker.record_datapoint(
                metric=EvolutionMetric.LATENCY,
                value=v,
            )

        trend = tracker.get_current_trend(EvolutionMetric.LATENCY)

        assert trend.volatility > 0
        assert 0 <= trend.stability_score <= 100

    def test_domain_trend(self):
        """Test getting domain-specific trend."""
        tracker = RuntimeEvolutionTracker()

        # Record for different domains
        for i in range(5):
            tracker.record_datapoint(
                metric=EvolutionMetric.CONTEXT_QUALITY,
                value=0.9 - (i * 0.02),
                domain="research",
            )
            tracker.record_datapoint(
                metric=EvolutionMetric.CONTEXT_QUALITY,
                value=0.8 - (i * 0.03),
                domain="code",
            )

        research_trend = tracker.get_domain_trend(
            EvolutionMetric.CONTEXT_QUALITY, "research"
        )
        code_trend = tracker.get_domain_trend(EvolutionMetric.CONTEXT_QUALITY, "code")

        assert len(research_trend.data_points) == 5
        assert len(code_trend.data_points) == 5
        assert research_trend.end_value > code_trend.end_value

    def test_provider_trend(self):
        """Test getting provider-specific trend."""
        tracker = RuntimeEvolutionTracker()

        # Record for different providers
        for i in range(5):
            tracker.record_datapoint(
                metric=EvolutionMetric.PROVIDER_QUALITY,
                value=0.92 - (i * 0.01),
                provider="claude",
            )
            tracker.record_datapoint(
                metric=EvolutionMetric.PROVIDER_QUALITY,
                value=0.88 - (i * 0.02),
                provider="openai",
            )

        claude_trend = tracker.get_provider_trend(
            EvolutionMetric.PROVIDER_QUALITY, "claude"
        )
        openai_trend = tracker.get_provider_trend(
            EvolutionMetric.PROVIDER_QUALITY, "openai"
        )

        assert len(claude_trend.data_points) == 5
        assert len(openai_trend.data_points) == 5

    def test_analyze_period(self):
        """Test analyzing a time period."""
        tracker = RuntimeEvolutionTracker()

        # Record data for 2 hours
        start_time = datetime.utcnow() - timedelta(hours=2)
        end_time = datetime.utcnow()

        for i in range(20):
            dp = EvolutionDataPoint(
                timestamp=start_time + timedelta(minutes=i * 6),  # Every 6 minutes
                metric=EvolutionMetric.CONTEXT_QUALITY,
                value=1.0 - (i * 0.02),
            )
            tracker.all_data_points.append(dp)

        period = tracker.analyze_period(start_time, end_time)

        assert period.period_id is not None
        assert period.duration_hours > 0
        assert len(period.trends) > 0

    def test_period_critical_degradation_detection(self):
        """Test detecting critical degradation in period."""
        tracker = RuntimeEvolutionTracker()

        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()

        # Record severe degradation
        for i in range(10):
            dp = EvolutionDataPoint(
                timestamp=start_time + timedelta(minutes=i * 6),
                metric=EvolutionMetric.SEMANTIC_RETENTION,
                value=1.0 - (i * 0.05),  # 50% total degradation
            )
            tracker.all_data_points.append(dp)

        period = tracker.analyze_period(start_time, end_time)

        assert period.critical_degradation_detected is True
        assert EvolutionMetric.SEMANTIC_RETENTION.value in [
            m for m in period.critical_metrics
        ]

    def test_domain_analysis_in_period(self):
        """Test domain-specific analysis in period."""
        tracker = RuntimeEvolutionTracker()

        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()

        # Record for multiple domains
        for i in range(10):
            for domain in ["research", "code", "design"]:
                dp = EvolutionDataPoint(
                    timestamp=start_time + timedelta(minutes=i * 6),
                    metric=EvolutionMetric.CONTEXT_QUALITY,
                    value=0.9 - (i * 0.02),
                    domain=domain,
                )
                tracker.all_data_points.append(dp)

        period = tracker.analyze_period(start_time, end_time)

        assert len(period.domain_trends) == 3
        assert "research" in period.domain_trends

    def test_provider_analysis_in_period(self):
        """Test provider-specific analysis in period."""
        tracker = RuntimeEvolutionTracker()

        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()

        # Record for multiple providers
        for i in range(10):
            for provider in ["claude", "openai", "gemini"]:
                dp = EvolutionDataPoint(
                    timestamp=start_time + timedelta(minutes=i * 6),
                    metric=EvolutionMetric.PROVIDER_QUALITY,
                    value=0.85 - (i * 0.01),
                    provider=provider,
                )
                tracker.all_data_points.append(dp)

        period = tracker.analyze_period(start_time, end_time)

        assert len(period.provider_trends) == 3
        assert "claude" in period.provider_trends

    def test_period_overall_stability(self):
        """Test overall stability calculation in period."""
        tracker = RuntimeEvolutionTracker()

        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()

        # Record stable data
        for i in range(10):
            dp = EvolutionDataPoint(
                timestamp=start_time + timedelta(minutes=i * 6),
                metric=EvolutionMetric.CONTEXT_QUALITY,
                value=0.85,
            )
            tracker.all_data_points.append(dp)

        period = tracker.analyze_period(start_time, end_time)

        assert period.overall_stability > 0
        assert period.overall_stability <= 100

    def test_completed_periods_accumulation(self):
        """Test that completed periods are accumulated."""
        tracker = RuntimeEvolutionTracker()

        # Add data points first
        base_time = datetime.utcnow() - timedelta(hours=4)
        for i in range(30):
            dp = EvolutionDataPoint(
                timestamp=base_time + timedelta(minutes=i * 5),
                metric=EvolutionMetric.CONTEXT_QUALITY,
                value=0.9 - (i * 0.01),
            )
            tracker.all_data_points.append(dp)

        # Now analyze periods
        for i in range(3):
            start = base_time + timedelta(hours=i)
            end = start + timedelta(hours=1)
            tracker.analyze_period(start, end)

        assert len(tracker.completed_periods) == 3

    def test_get_summary(self):
        """Test getting summary of evolution."""
        tracker = RuntimeEvolutionTracker()

        # Record some data
        for i in range(10):
            tracker.record_datapoint(
                metric=EvolutionMetric.CONTEXT_QUALITY,
                value=0.9 - (i * 0.02),
            )

        summary = tracker.get_summary()

        assert summary["total_datapoints"] == 10
        assert summary["tracking_window_hours"] == 24
        assert "metrics" in summary

    def test_empty_summary(self):
        """Test summary with no data."""
        tracker = RuntimeEvolutionTracker()
        summary = tracker.get_summary()

        assert summary["status"] == "no_data"

    def test_get_evolution_tracker_singleton(self):
        """Test getting evolution tracker as singleton."""
        tracker1 = get_evolution_tracker()
        tracker2 = get_evolution_tracker()

        assert tracker1 is tracker2

    def test_tracking_window_filtering(self):
        """Test that tracking window correctly filters old data."""
        tracker = RuntimeEvolutionTracker(tracking_window_hours=1)

        # Add recent data
        tracker.record_datapoint(
            metric=EvolutionMetric.CONTEXT_QUALITY,
            value=0.9,
        )

        # Add old data
        old_dp = EvolutionDataPoint(
            timestamp=datetime.utcnow() - timedelta(hours=2),
            metric=EvolutionMetric.CONTEXT_QUALITY,
            value=0.5,
        )
        tracker.all_data_points.append(old_dp)

        trend = tracker.get_current_trend(EvolutionMetric.CONTEXT_QUALITY)

        # Only recent data should be in trend
        assert len(trend.data_points) == 1
        assert trend.start_value == 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
