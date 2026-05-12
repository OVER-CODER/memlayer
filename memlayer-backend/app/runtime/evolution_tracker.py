"""
Runtime Evolution Tracker for Phase 5B.

Tracks longitudinal semantic degradation and evolution of runtime characteristics:
- Context quality trends over time
- Token efficiency evolution
- Provider adaptation curves
- Memory compression effectiveness
- Semantic retention degradation patterns
- Entity preservation over time
- Domain-specific performance trends
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class EvolutionMetric(str, Enum):
    """Metrics tracked for runtime evolution."""

    CONTEXT_QUALITY = "context_quality"
    TOKEN_EFFICIENCY = "token_efficiency"
    SEMANTIC_RETENTION = "semantic_retention"
    ENTITY_PRESERVATION = "entity_preservation"
    COMPRESSION_RATIO = "compression_ratio"
    LATENCY = "latency"
    PROVIDER_QUALITY = "provider_quality"
    MEMORY_RELEVANCE = "memory_relevance"


@dataclass
class EvolutionDataPoint:
    """A single data point in evolution tracking."""

    timestamp: datetime
    metric: EvolutionMetric
    value: float
    domain: Optional[str] = None  # Domain-specific measurement
    provider: Optional[str] = None  # Provider-specific measurement
    context: Dict[str, Any] = field(
        default_factory=dict
    )  # Additional context (e.g., query_complexity, memory_size)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "metric": self.metric.value,
            "value": self.value,
            "domain": self.domain,
            "provider": self.provider,
            "context": self.context,
        }


@dataclass
class EvolutionTrend:
    """Analysis of a metric's trend over time."""

    metric: EvolutionMetric
    data_points: List[EvolutionDataPoint] = field(default_factory=list)

    # Trend characteristics
    start_value: float = 0.0
    end_value: float = 0.0
    min_value: float = 1.0
    max_value: float = 0.0
    avg_value: float = 0.0

    # Degradation analysis
    degradation_rate: float = 0.0  # per hour
    total_degradation: float = 0.0
    degradation_type: str = "unknown"  # linear, exponential, stepwise, stable

    # Volatility
    volatility: float = 0.0  # Standard deviation of values
    stability_score: float = 100.0  # 0-100

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "metric": self.metric.value,
            "data_point_count": len(self.data_points),
            "start_value": self.start_value,
            "end_value": self.end_value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "avg_value": self.avg_value,
            "degradation_rate": self.degradation_rate,
            "total_degradation": self.total_degradation,
            "degradation_type": self.degradation_type,
            "volatility": self.volatility,
            "stability_score": self.stability_score,
        }


@dataclass
class EvolutionPeriod:
    """A period of runtime evolution analysis."""

    period_id: str
    start_time: datetime
    end_time: datetime
    duration_hours: float

    # Trends for each metric
    trends: Dict[EvolutionMetric, EvolutionTrend] = field(default_factory=dict)

    # Domain-specific analysis
    domain_trends: Dict[str, Dict[EvolutionMetric, EvolutionTrend]] = field(
        default_factory=dict
    )

    # Provider-specific analysis
    provider_trends: Dict[str, Dict[EvolutionMetric, EvolutionTrend]] = field(
        default_factory=dict
    )

    # Overall period assessment
    overall_stability: float = 0.0  # 0-100
    critical_degradation_detected: bool = False
    critical_metrics: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "period_id": self.period_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_hours": self.duration_hours,
            "trends": {k.value: v.to_dict() for k, v in self.trends.items()},
            "overall_stability": self.overall_stability,
            "critical_degradation_detected": self.critical_degradation_detected,
            "critical_metrics": self.critical_metrics,
        }


class RuntimeEvolutionTracker:
    """
    Tracks runtime evolution and degradation over time.

    Monitors:
    - Long-term quality degradation
    - Provider adaptation effectiveness
    - Domain-specific performance trends
    - Memory compression evolution
    - Entity preservation over time
    """

    def __init__(self, tracking_window_hours: int = 24):
        """
        Initialize evolution tracker.

        Args:
            tracking_window_hours: Hours to track for trend analysis
        """
        self.tracking_window_hours = tracking_window_hours
        self.all_data_points: List[EvolutionDataPoint] = []
        self.completed_periods: List[EvolutionPeriod] = []
        self.current_period_start: Optional[datetime] = None

        logger.info(
            f"Runtime Evolution Tracker initialized ({tracking_window_hours}h window)"
        )

    def record_datapoint(
        self,
        metric: EvolutionMetric,
        value: float,
        domain: Optional[str] = None,
        provider: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvolutionDataPoint:
        """
        Record a data point for evolution tracking.

        Args:
            metric: Metric being tracked
            value: Metric value
            domain: Optional domain classification
            provider: Optional provider classification
            context: Optional additional context

        Returns:
            Recorded EvolutionDataPoint
        """
        datapoint = EvolutionDataPoint(
            timestamp=datetime.utcnow(),
            metric=metric,
            value=value,
            domain=domain,
            provider=provider,
            context=context or {},
        )

        self.all_data_points.append(datapoint)

        if self.current_period_start is None:
            self.current_period_start = datetime.utcnow()

        logger.debug(
            f"Recorded {metric.value}={value:.3f} "
            f"(domain={domain}, provider={provider})"
        )

        return datapoint

    def get_current_trend(self, metric: EvolutionMetric) -> EvolutionTrend:
        """
        Get current trend for a metric within tracking window.

        Args:
            metric: Metric to analyze

        Returns:
            EvolutionTrend with current analysis
        """
        # Get recent data points
        cutoff_time = datetime.utcnow() - timedelta(hours=self.tracking_window_hours)
        relevant_points = [
            dp
            for dp in self.all_data_points
            if dp.metric == metric and dp.timestamp >= cutoff_time
        ]

        trend = EvolutionTrend(metric=metric, data_points=relevant_points)

        if not relevant_points:
            return trend

        # Calculate statistics
        values = [dp.value for dp in relevant_points]
        trend.start_value = values[0]
        trend.end_value = values[-1]
        trend.min_value = min(values)
        trend.max_value = max(values)
        trend.avg_value = sum(values) / len(values)

        # Calculate degradation
        time_delta = (
            relevant_points[-1].timestamp - relevant_points[0].timestamp
        ).total_seconds() / 3600  # hours
        if time_delta > 0:
            trend.degradation_rate = (trend.end_value - trend.start_value) / time_delta
            trend.total_degradation = trend.start_value - trend.end_value

            # Determine degradation type
            trend.degradation_type = self._classify_degradation_type(values, time_delta)
        else:
            trend.degradation_type = "instantaneous"

        # Calculate volatility
        if len(values) > 1:
            mean = trend.avg_value
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            trend.volatility = variance**0.5

            # Stability score (lower volatility = higher stability)
            trend.stability_score = max(0.0, 100.0 - (trend.volatility * 100))

        return trend

    def get_domain_trend(self, metric: EvolutionMetric, domain: str) -> EvolutionTrend:
        """
        Get trend for a specific domain.

        Args:
            metric: Metric to analyze
            domain: Domain to filter by

        Returns:
            EvolutionTrend for the domain
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=self.tracking_window_hours)
        relevant_points = [
            dp
            for dp in self.all_data_points
            if dp.metric == metric
            and dp.domain == domain
            and dp.timestamp >= cutoff_time
        ]

        trend = EvolutionTrend(metric=metric, data_points=relevant_points)

        if relevant_points:
            values = [dp.value for dp in relevant_points]
            trend.start_value = values[0]
            trend.end_value = values[-1]
            trend.min_value = min(values)
            trend.max_value = max(values)
            trend.avg_value = sum(values) / len(values)
            trend.total_degradation = trend.start_value - trend.end_value

        return trend

    def get_provider_trend(
        self, metric: EvolutionMetric, provider: str
    ) -> EvolutionTrend:
        """
        Get trend for a specific provider.

        Args:
            metric: Metric to analyze
            provider: Provider to filter by

        Returns:
            EvolutionTrend for the provider
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=self.tracking_window_hours)
        relevant_points = [
            dp
            for dp in self.all_data_points
            if dp.metric == metric
            and dp.provider == provider
            and dp.timestamp >= cutoff_time
        ]

        trend = EvolutionTrend(metric=metric, data_points=relevant_points)

        if relevant_points:
            values = [dp.value for dp in relevant_points]
            trend.start_value = values[0]
            trend.end_value = values[-1]
            trend.min_value = min(values)
            trend.max_value = max(values)
            trend.avg_value = sum(values) / len(values)
            trend.total_degradation = trend.start_value - trend.end_value

        return trend

    def analyze_period(
        self, period_start: datetime, period_end: datetime
    ) -> EvolutionPeriod:
        """
        Analyze runtime evolution for a specific period.

        Args:
            period_start: Period start time
            period_end: Period end time

        Returns:
            EvolutionPeriod with complete analysis
        """
        period_id = f"period-{period_start.isoformat()[:13]}"
        duration_hours = (period_end - period_start).total_seconds() / 3600

        period = EvolutionPeriod(
            period_id=period_id,
            start_time=period_start,
            end_time=period_end,
            duration_hours=duration_hours,
        )

        # Get relevant data points
        relevant_points = [
            dp
            for dp in self.all_data_points
            if period_start <= dp.timestamp <= period_end
        ]

        if not relevant_points:
            return period

        # Analyze each metric
        for metric in EvolutionMetric:
            metric_points = [dp for dp in relevant_points if dp.metric == metric]
            if metric_points:
                trend = EvolutionTrend(metric=metric, data_points=metric_points)
                values = [dp.value for dp in metric_points]
                trend.start_value = values[0]
                trend.end_value = values[-1]
                trend.min_value = min(values)
                trend.max_value = max(values)
                trend.avg_value = sum(values) / len(values)

                time_delta = (
                    metric_points[-1].timestamp - metric_points[0].timestamp
                ).total_seconds() / 3600
                if time_delta > 0:
                    trend.degradation_rate = (
                        trend.end_value - trend.start_value
                    ) / time_delta
                    trend.total_degradation = trend.start_value - trend.end_value

                if len(values) > 1:
                    mean = trend.avg_value
                    variance = sum((v - mean) ** 2 for v in values) / len(values)
                    trend.volatility = variance**0.5
                    trend.stability_score = max(0.0, 100.0 - (trend.volatility * 100))

                period.trends[metric] = trend

                # Check for critical degradation
                if trend.total_degradation > 0.2:  # > 20% degradation
                    period.critical_degradation_detected = True
                    period.critical_metrics.append(metric.value)

        # Analyze by domain
        unique_domains = set(dp.domain for dp in relevant_points if dp.domain)
        for domain in unique_domains:
            domain_points = [dp for dp in relevant_points if dp.domain == domain]
            domain_trends = {}

            for metric in EvolutionMetric:
                metric_points = [dp for dp in domain_points if dp.metric == metric]
                if metric_points:
                    trend = EvolutionTrend(metric=metric, data_points=metric_points)
                    values = [dp.value for dp in metric_points]
                    trend.start_value = values[0]
                    trend.end_value = values[-1]
                    trend.avg_value = sum(values) / len(values)
                    domain_trends[metric] = trend

            if domain_trends:
                period.domain_trends[domain] = domain_trends

        # Analyze by provider
        unique_providers = set(dp.provider for dp in relevant_points if dp.provider)
        for provider in unique_providers:
            provider_points = [dp for dp in relevant_points if dp.provider == provider]
            provider_trends = {}

            for metric in EvolutionMetric:
                metric_points = [dp for dp in provider_points if dp.metric == metric]
                if metric_points:
                    trend = EvolutionTrend(metric=metric, data_points=metric_points)
                    values = [dp.value for dp in metric_points]
                    trend.start_value = values[0]
                    trend.end_value = values[-1]
                    trend.avg_value = sum(values) / len(values)
                    provider_trends[metric] = trend

            if provider_trends:
                period.provider_trends[provider] = provider_trends

        # Calculate overall stability
        if period.trends:
            stability_scores = [t.stability_score for t in period.trends.values()]
            period.overall_stability = sum(stability_scores) / len(stability_scores)

        self.completed_periods.append(period)
        return period

    def _classify_degradation_type(self, values: List[float], time_delta: float) -> str:
        """Classify type of degradation in values."""
        if len(values) < 2:
            return "insufficient_data"

        # Check for linear degradation
        linear_fit = self._linear_fit(values)
        slope = linear_fit["slope"]

        # Check for exponential-like degradation
        if len(values) > 5:
            first_half_avg = sum(values[: len(values) // 2]) / (len(values) // 2)
            second_half_avg = sum(values[len(values) // 2 :]) / (
                len(values) - len(values) // 2
            )
            acceleration = (
                (second_half_avg - first_half_avg) / first_half_avg
                if first_half_avg != 0
                else 0
            )

            if acceleration < -0.05:  # Accelerating degradation
                return "exponential"

        if abs(slope) < 0.001:
            return "stable"
        elif slope < -0.05:
            return "linear"
        else:
            return "improving"

    def _linear_fit(self, values: List[float]) -> Dict[str, float]:
        """Simple linear regression fit."""
        n = len(values)
        if n < 2:
            return {"slope": 0.0, "intercept": 0.0}

        x = list(range(n))
        mean_x = sum(x) / n
        mean_y = sum(values) / n

        numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0.0
        intercept = mean_y - slope * mean_x

        return {"slope": slope, "intercept": intercept}

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of tracked evolution."""
        if not self.all_data_points:
            return {"status": "no_data"}

        metrics_summary = {}
        for metric in EvolutionMetric:
            trend = self.get_current_trend(metric)
            metrics_summary[metric.value] = trend.to_dict()

        return {
            "total_datapoints": len(self.all_data_points),
            "tracking_window_hours": self.tracking_window_hours,
            "completed_periods": len(self.completed_periods),
            "metrics": metrics_summary,
        }


# Global tracker instance
_evolution_tracker: Optional[RuntimeEvolutionTracker] = None


def get_evolution_tracker() -> RuntimeEvolutionTracker:
    """Get or create the global evolution tracker."""
    global _evolution_tracker
    if _evolution_tracker is None:
        _evolution_tracker = RuntimeEvolutionTracker()
    return _evolution_tracker
