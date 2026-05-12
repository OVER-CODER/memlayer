"""
Regression Replay & Comparison Suite for Phase 5B.

Provides comprehensive cross-version trace comparison, semantic regression detection,
performance improvement validation, and regression severity analysis.

Enables:
- Cross-version trace comparison with delta analysis
- Semantic regression detection across compiler versions
- Performance improvement validation and benchmarking
- Regression severity scoring and categorization
- Provider stability analysis across versions
- Regression history tracking and trending
"""

from typing import List, Dict, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import logging
import hashlib
import json

logger = logging.getLogger(__name__)


class RegressionType(Enum):
    """Categories of detected regressions."""

    QUALITY_DEGRADATION = "quality_degradation"
    SEMANTIC_LOSS = "semantic_loss"
    TOKEN_INEFFICIENCY = "token_inefficiency"
    LATENCY_REGRESSION = "latency_regression"
    PROVIDER_QUALITY_SHIFT = "provider_quality_shift"
    COMPRESSION_INEFFICIENCY = "compression_inefficiency"
    MEMORY_DEGRADATION = "memory_degradation"
    CONSISTENCY_VIOLATION = "consistency_violation"
    UNKNOWN = "unknown"


class RegressionSeverity(Enum):
    """Severity levels for detected regressions."""

    CRITICAL = 5  # System-breaking, requires immediate fix
    HIGH = 4  # Significant degradation (>10%), impacts production
    MEDIUM = 3  # Moderate degradation (5-10%), needs investigation
    LOW = 2  # Minor degradation (<5%), monitor
    TRIVIAL = 1  # Negligible impact (<1%), informational


@dataclass
class RegressionEvent:
    """Single regression detection event."""

    event_id: str
    timestamp: datetime

    # Trace identification
    baseline_trace_id: str
    comparison_trace_id: str

    # Versioning
    baseline_version: str
    comparison_version: str

    # Regression classification
    regression_type: RegressionType
    severity: RegressionSeverity

    # Metric deltas
    quality_delta: float = 0.0  # Negative = regression
    semantic_delta: float = 0.0
    token_efficiency_delta: float = 0.0
    latency_delta_ms: float = 0.0

    # Context
    provider: str = ""
    compression_mode: str = ""
    query_type: str = ""
    domain: str = ""

    # Details
    description: str = ""
    affected_metrics: List[str] = field(default_factory=list)
    root_cause_indicators: List[str] = field(default_factory=list)

    # Impact assessment
    estimated_impact: float = 0.0  # 0-100, percentage impact
    user_visible: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "baseline_trace_id": self.baseline_trace_id,
            "comparison_trace_id": self.comparison_trace_id,
            "baseline_version": self.baseline_version,
            "comparison_version": self.comparison_version,
            "regression_type": self.regression_type.value,
            "severity": self.severity.name,
            "quality_delta": self.quality_delta,
            "semantic_delta": self.semantic_delta,
            "token_efficiency_delta": self.token_efficiency_delta,
            "latency_delta_ms": self.latency_delta_ms,
            "provider": self.provider,
            "compression_mode": self.compression_mode,
            "query_type": self.query_type,
            "domain": self.domain,
            "description": self.description,
            "affected_metrics": self.affected_metrics,
            "root_cause_indicators": self.root_cause_indicators,
            "estimated_impact": self.estimated_impact,
            "user_visible": self.user_visible,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegressionEvent":
        """Rehydrate event from dictionary."""
        return cls(
            event_id=data["event_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            baseline_trace_id=data.get("baseline_trace_id", ""),
            comparison_trace_id=data.get("comparison_trace_id", ""),
            baseline_version=data.get("baseline_version", ""),
            comparison_version=data.get("comparison_version", ""),
            regression_type=RegressionType(
                data.get("regression_type", RegressionType.UNKNOWN.value)
            ),
            severity=RegressionSeverity[data.get("severity", "LOW")],
            quality_delta=float(data.get("quality_delta", 0.0)),
            semantic_delta=float(data.get("semantic_delta", 0.0)),
            token_efficiency_delta=float(data.get("token_efficiency_delta", 0.0)),
            latency_delta_ms=float(data.get("latency_delta_ms", 0.0)),
            provider=data.get("provider", ""),
            compression_mode=data.get("compression_mode", ""),
            query_type=data.get("query_type", ""),
            domain=data.get("domain", ""),
            description=data.get("description", ""),
            affected_metrics=list(data.get("affected_metrics", [])),
            root_cause_indicators=list(data.get("root_cause_indicators", [])),
            estimated_impact=float(data.get("estimated_impact", 0.0)),
            user_visible=bool(data.get("user_visible", False)),
        )


@dataclass
class CrossVersionComparison:
    """Result of comparing traces across versions."""

    comparison_id: str
    timestamp: datetime

    # Version info
    baseline_version: str
    comparison_version: str

    # Trace counts
    baseline_traces: int = 0
    comparison_traces: int = 0
    comparable_traces: int = 0

    # Overall metrics
    average_quality_delta: float = 0.0
    average_semantic_delta: float = 0.0
    average_token_efficiency_delta: float = 0.0
    average_latency_delta_ms: float = 0.0

    # Regression statistics
    total_regressions: int = 0
    critical_regressions: int = 0
    high_regressions: int = 0
    medium_regressions: int = 0
    low_regressions: int = 0

    # Performance improvements
    total_improvements: int = 0
    quality_improvements: int = 0
    latency_improvements: int = 0
    token_improvements: int = 0

    # Provider analysis
    provider_regressions: Dict[str, int] = field(default_factory=dict)
    provider_improvements: Dict[str, int] = field(default_factory=dict)
    most_affected_provider: str = ""
    best_improved_provider: str = ""

    # Domain analysis
    domain_regressions: Dict[str, int] = field(default_factory=dict)
    domain_improvements: Dict[str, int] = field(default_factory=dict)

    # Overall verdict
    is_regression_overall: bool = False
    regression_confidence: float = 0.0  # 0-1
    recommendation: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "comparison_id": self.comparison_id,
            "timestamp": self.timestamp.isoformat(),
            "baseline_version": self.baseline_version,
            "comparison_version": self.comparison_version,
            "baseline_traces": self.baseline_traces,
            "comparison_traces": self.comparison_traces,
            "comparable_traces": self.comparable_traces,
            "average_quality_delta": self.average_quality_delta,
            "average_semantic_delta": self.average_semantic_delta,
            "average_token_efficiency_delta": self.average_token_efficiency_delta,
            "average_latency_delta_ms": self.average_latency_delta_ms,
            "total_regressions": self.total_regressions,
            "critical_regressions": self.critical_regressions,
            "high_regressions": self.high_regressions,
            "medium_regressions": self.medium_regressions,
            "low_regressions": self.low_regressions,
            "total_improvements": self.total_improvements,
            "quality_improvements": self.quality_improvements,
            "latency_improvements": self.latency_improvements,
            "token_improvements": self.token_improvements,
            "provider_regressions": self.provider_regressions,
            "provider_improvements": self.provider_improvements,
            "most_affected_provider": self.most_affected_provider,
            "best_improved_provider": self.best_improved_provider,
            "domain_regressions": self.domain_regressions,
            "domain_improvements": self.domain_improvements,
            "is_regression_overall": self.is_regression_overall,
            "regression_confidence": self.regression_confidence,
            "recommendation": self.recommendation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CrossVersionComparison":
        """Rehydrate comparison from dictionary."""
        return cls(
            comparison_id=data["comparison_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            baseline_version=data.get("baseline_version", ""),
            comparison_version=data.get("comparison_version", ""),
            baseline_traces=int(data.get("baseline_traces", 0)),
            comparison_traces=int(data.get("comparison_traces", 0)),
            comparable_traces=int(data.get("comparable_traces", 0)),
            average_quality_delta=float(data.get("average_quality_delta", 0.0)),
            average_semantic_delta=float(data.get("average_semantic_delta", 0.0)),
            average_token_efficiency_delta=float(
                data.get("average_token_efficiency_delta", 0.0)
            ),
            average_latency_delta_ms=float(data.get("average_latency_delta_ms", 0.0)),
            total_regressions=int(data.get("total_regressions", 0)),
            critical_regressions=int(data.get("critical_regressions", 0)),
            high_regressions=int(data.get("high_regressions", 0)),
            medium_regressions=int(data.get("medium_regressions", 0)),
            low_regressions=int(data.get("low_regressions", 0)),
            total_improvements=int(data.get("total_improvements", 0)),
            quality_improvements=int(data.get("quality_improvements", 0)),
            latency_improvements=int(data.get("latency_improvements", 0)),
            token_improvements=int(data.get("token_improvements", 0)),
            provider_regressions=dict(data.get("provider_regressions", {})),
            provider_improvements=dict(data.get("provider_improvements", {})),
            most_affected_provider=data.get("most_affected_provider", ""),
            best_improved_provider=data.get("best_improved_provider", ""),
            domain_regressions=dict(data.get("domain_regressions", {})),
            domain_improvements=dict(data.get("domain_improvements", {})),
            is_regression_overall=bool(data.get("is_regression_overall", False)),
            regression_confidence=float(data.get("regression_confidence", 0.0)),
            recommendation=data.get("recommendation", ""),
        )


@dataclass
class ProviderVersionAnalysis:
    """Analysis of provider behavior across versions."""

    provider: str
    baseline_version: str
    comparison_version: str

    # Trace counts
    baseline_traces: int = 0
    comparison_traces: int = 0

    # Quality metrics
    baseline_avg_quality: float = 0.0
    comparison_avg_quality: float = 0.0
    quality_delta: float = 0.0

    # Stability
    baseline_quality_variance: float = 0.0
    comparison_quality_variance: float = 0.0
    stability_change: float = 0.0

    # Latency analysis
    baseline_avg_latency_ms: float = 0.0
    comparison_avg_latency_ms: float = 0.0
    latency_delta: float = 0.0

    # Token efficiency
    baseline_avg_token_efficiency: float = 0.0
    comparison_avg_token_efficiency: float = 0.0
    token_efficiency_delta: float = 0.0

    # Regression count
    regressions: int = 0
    improvements: int = 0

    # Provider status
    status_change: str = ""  # "degraded", "stable", "improved", "unknown"

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "provider": self.provider,
            "baseline_version": self.baseline_version,
            "comparison_version": self.comparison_version,
            "baseline_traces": self.baseline_traces,
            "comparison_traces": self.comparison_traces,
            "baseline_avg_quality": self.baseline_avg_quality,
            "comparison_avg_quality": self.comparison_avg_quality,
            "quality_delta": self.quality_delta,
            "baseline_quality_variance": self.baseline_quality_variance,
            "comparison_quality_variance": self.comparison_quality_variance,
            "stability_change": self.stability_change,
            "baseline_avg_latency_ms": self.baseline_avg_latency_ms,
            "comparison_avg_latency_ms": self.comparison_avg_latency_ms,
            "latency_delta": self.latency_delta,
            "baseline_avg_token_efficiency": self.baseline_avg_token_efficiency,
            "comparison_avg_token_efficiency": self.comparison_avg_token_efficiency,
            "token_efficiency_delta": self.token_efficiency_delta,
            "regressions": self.regressions,
            "improvements": self.improvements,
            "status_change": self.status_change,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderVersionAnalysis":
        """Rehydrate provider version analysis from dictionary."""
        return cls(
            provider=data.get("provider", ""),
            baseline_version=data.get("baseline_version", ""),
            comparison_version=data.get("comparison_version", ""),
            baseline_traces=int(data.get("baseline_traces", 0)),
            comparison_traces=int(data.get("comparison_traces", 0)),
            baseline_avg_quality=float(data.get("baseline_avg_quality", 0.0)),
            comparison_avg_quality=float(data.get("comparison_avg_quality", 0.0)),
            quality_delta=float(data.get("quality_delta", 0.0)),
            baseline_quality_variance=float(
                data.get("baseline_quality_variance", 0.0)
            ),
            comparison_quality_variance=float(
                data.get("comparison_quality_variance", 0.0)
            ),
            stability_change=float(data.get("stability_change", 0.0)),
            baseline_avg_latency_ms=float(data.get("baseline_avg_latency_ms", 0.0)),
            comparison_avg_latency_ms=float(
                data.get("comparison_avg_latency_ms", 0.0)
            ),
            latency_delta=float(data.get("latency_delta", 0.0)),
            baseline_avg_token_efficiency=float(
                data.get("baseline_avg_token_efficiency", 0.0)
            ),
            comparison_avg_token_efficiency=float(
                data.get("comparison_avg_token_efficiency", 0.0)
            ),
            token_efficiency_delta=float(data.get("token_efficiency_delta", 0.0)),
            regressions=int(data.get("regressions", 0)),
            improvements=int(data.get("improvements", 0)),
            status_change=data.get("status_change", ""),
        )


class RegressionDetector:
    """
    Detects and analyzes regressions between trace versions.

    Provides:
    - Regression detection with configurable thresholds
    - Severity scoring and categorization
    - Root cause indication
    - Impact assessment
    """

    def __init__(
        self,
        quality_threshold: float = 0.05,
        latency_threshold: float = 0.10,
        semantic_threshold: float = 0.08,
        token_threshold: float = 0.10,
    ):
        """
        Initialize regression detector.

        Args:
            quality_threshold: Quality regression threshold (default 5%)
            latency_threshold: Latency regression threshold (default 10%)
            semantic_threshold: Semantic loss threshold (default 8%)
            token_threshold: Token efficiency threshold (default 10%)
        """
        self.quality_threshold = quality_threshold
        self.latency_threshold = latency_threshold
        self.semantic_threshold = semantic_threshold
        self.token_threshold = token_threshold
        self.detected_regressions: List[RegressionEvent] = []

    def detect_regression(
        self,
        baseline_trace: Dict,
        comparison_trace: Dict,
        baseline_version: str,
        comparison_version: str,
        event_id: str,
    ) -> Optional[RegressionEvent]:
        """
        Detect regression between two traces.

        Args:
            baseline_trace: Baseline trace metrics
            comparison_trace: Comparison trace metrics
            baseline_version: Baseline version identifier
            comparison_version: Comparison version identifier
            event_id: Unique event identifier

        Returns:
            RegressionEvent if regression detected, None otherwise
        """
        # Calculate deltas
        quality_delta = comparison_trace.get("quality_score", 0.0) - baseline_trace.get(
            "quality_score", 0.0
        )
        semantic_delta = comparison_trace.get(
            "semantic_retention", 0.0
        ) - baseline_trace.get("semantic_retention", 0.0)
        token_delta = comparison_trace.get(
            "token_efficiency", 0.0
        ) - baseline_trace.get("token_efficiency", 0.0)
        latency_delta = comparison_trace.get(
            "total_duration_ms", 0.0
        ) - baseline_trace.get("total_duration_ms", 0.0)
        quality_delta = round(quality_delta, 10)
        semantic_delta = round(semantic_delta, 10)
        token_delta = round(token_delta, 10)
        latency_delta = round(latency_delta, 10)

        # Determine regression type and severity
        regression_type, severity, description, affected_metrics = (
            self._classify_regression(
                quality_delta,
                semantic_delta,
                token_delta,
                latency_delta,
                baseline_trace,
                comparison_trace,
            )
        )

        if regression_type == RegressionType.UNKNOWN:
            return None

        # Create regression event
        event = RegressionEvent(
            event_id=event_id,
            timestamp=datetime.now(timezone.utc),
            baseline_trace_id=baseline_trace.get("trace_id", ""),
            comparison_trace_id=comparison_trace.get("trace_id", ""),
            baseline_version=baseline_version,
            comparison_version=comparison_version,
            regression_type=regression_type,
            severity=severity,
            quality_delta=quality_delta,
            semantic_delta=semantic_delta,
            token_efficiency_delta=token_delta,
            latency_delta_ms=latency_delta,
            provider=baseline_trace.get("provider", ""),
            compression_mode=baseline_trace.get("compression_mode", ""),
            query_type=baseline_trace.get("query_type", ""),
            domain=baseline_trace.get("domain", ""),
            description=description,
            affected_metrics=affected_metrics,
        )

        # Identify root causes
        event.root_cause_indicators = self._identify_root_causes(
            baseline_trace,
            comparison_trace,
            quality_delta,
            semantic_delta,
            token_delta,
            latency_delta,
        )

        # Estimate impact
        event.estimated_impact = self._estimate_impact(
            quality_delta, semantic_delta, token_delta, latency_delta
        )
        event.user_visible = severity in [
            RegressionSeverity.CRITICAL,
            RegressionSeverity.HIGH,
        ]

        self.detected_regressions.append(event)
        return event

    def _classify_regression(
        self,
        quality_delta: float,
        semantic_delta: float,
        token_delta: float,
        latency_delta: float,
        baseline_trace: Dict,
        comparison_trace: Dict,
    ) -> Tuple[RegressionType, RegressionSeverity, str, List[str]]:
        """
        Classify regression type and severity.

        Returns:
            Tuple of (RegressionType, RegressionSeverity, description, affected_metrics)
        """
        affected_metrics = []
        descriptions = []
        baseline_quality = float(baseline_trace.get("quality_score", 0.0))
        baseline_semantic = float(baseline_trace.get("semantic_retention", 0.0))
        baseline_token = float(baseline_trace.get("token_efficiency", 0.0))
        baseline_latency = float(baseline_trace.get("total_duration_ms", 0.0))

        quality_impact = (
            max(0.0, -quality_delta / baseline_quality) if baseline_quality > 0 else 0.0
        )
        semantic_impact = (
            max(0.0, -semantic_delta / baseline_semantic)
            if baseline_semantic > 0
            else 0.0
        )
        token_impact = (
            max(0.0, -token_delta / baseline_token) if baseline_token > 0 else 0.0
        )
        latency_impact = (
            max(0.0, latency_delta / baseline_latency) if baseline_latency > 0 else 0.0
        )

        # Check quality degradation
        if quality_impact > self.quality_threshold:
            affected_metrics.append("quality_score")
            descriptions.append(f"Quality degraded by {abs(quality_delta):.2%}")

        # Check semantic loss
        if semantic_impact > self.semantic_threshold:
            affected_metrics.append("semantic_retention")
            descriptions.append(f"Semantic retention lost {abs(semantic_delta):.2%}")

        # Check token efficiency regression
        if token_impact > self.token_threshold:
            affected_metrics.append("token_efficiency")
            descriptions.append(f"Token efficiency degraded by {abs(token_delta):.2%}")

        # Check latency regression
        if latency_impact > self.latency_threshold:
            affected_metrics.append("latency")
            descriptions.append(f"Latency increased by {latency_delta:.1f}ms")

        # Determine primary regression type
        regression_type = RegressionType.UNKNOWN
        if quality_impact > self.quality_threshold:
            regression_type = RegressionType.QUALITY_DEGRADATION
        elif semantic_impact > self.semantic_threshold:
            regression_type = RegressionType.SEMANTIC_LOSS
        elif token_impact > self.token_threshold:
            regression_type = RegressionType.COMPRESSION_INEFFICIENCY
        elif latency_impact > self.latency_threshold:
            regression_type = RegressionType.LATENCY_REGRESSION

        # Determine severity
        severity = self._calculate_severity(
            quality_delta,
            semantic_delta,
            token_delta,
            latency_delta,
            quality_impact,
            semantic_impact,
            token_impact,
            latency_impact,
        )

        description = (
            " | ".join(descriptions) if descriptions else "Minor regression detected"
        )

        return regression_type, severity, description, affected_metrics

    def _calculate_severity(
        self,
        quality_delta: float,
        semantic_delta: float,
        token_delta: float,
        latency_delta: float,
        quality_impact: float,
        semantic_impact: float,
        token_impact: float,
        latency_impact: float,
    ) -> RegressionSeverity:
        """Calculate severity based on deltas."""
        weighted_impact = (
            quality_impact * 0.4
            + semantic_impact * 0.35
            + token_impact * 0.15
            + latency_impact * 0.1
        )
        max_impact = max(quality_impact, semantic_impact, token_impact, latency_impact)

        if max_impact >= 0.30 or weighted_impact >= 0.20:
            return RegressionSeverity.CRITICAL
        elif max_impact >= 0.10 or weighted_impact >= 0.10:
            return RegressionSeverity.HIGH
        elif max_impact >= 0.05 or weighted_impact >= 0.05:
            return RegressionSeverity.MEDIUM
        elif max_impact >= 0.01 or weighted_impact >= 0.01:
            return RegressionSeverity.LOW
        else:
            return RegressionSeverity.TRIVIAL

    def _identify_root_causes(
        self,
        baseline_trace: Dict,
        comparison_trace: Dict,
        quality_delta: float,
        semantic_delta: float,
        token_delta: float,
        latency_delta: float,
    ) -> List[str]:
        """Identify potential root causes for regression."""
        causes = []

        # Token pressure
        baseline_tokens = baseline_trace.get("token_metrics", {}).get("total_tokens", 0)
        comparison_tokens = comparison_trace.get("token_metrics", {}).get(
            "total_tokens", 0
        )
        if comparison_tokens > baseline_tokens * 1.2:
            causes.append("increased_token_pressure")

        # Compression changes
        baseline_comp = baseline_trace.get("compression_mode", "")
        comparison_comp = comparison_trace.get("compression_mode", "")
        if baseline_comp != comparison_comp:
            causes.append("compression_mode_change")

        # Provider changes
        baseline_provider = baseline_trace.get("provider", "")
        comparison_provider = comparison_trace.get("provider", "")
        if baseline_provider != comparison_provider:
            causes.append("provider_change")

        # Increased memory usage
        baseline_memory_count = baseline_trace.get("memories_count", 0)
        comparison_memory_count = comparison_trace.get("memories_count", 0)
        if comparison_memory_count > baseline_memory_count * 1.3:
            causes.append("memory_bloat")

        # Quality thresholds
        if quality_delta < -0.20:
            causes.append("severe_quality_loss")

        if not causes:
            causes.append("undetermined")

        return causes

    def _estimate_impact(
        self,
        quality_delta: float,
        semantic_delta: float,
        token_delta: float,
        latency_delta: float,
    ) -> float:
        """Estimate percentage impact (0-100)."""
        impact = (
            abs(quality_delta) * 100 * 0.4
            + abs(semantic_delta) * 100 * 0.35
            + abs(token_delta) * 100 * 0.15
            + min(abs(latency_delta) / 10, 100) * 0.1
        )
        return min(impact, 100.0)


class CrossVersionComparator:
    """
    Compares traces across compiler versions.

    Provides:
    - Large-scale cross-version trace comparison
    - Provider-specific analysis
    - Domain-specific regression analysis
    - Performance improvement tracking
    - Overall verdict generation
    """

    def __init__(self, regression_detector: Optional[RegressionDetector] = None):
        """
        Initialize comparator.

        Args:
            regression_detector: Optional custom regression detector
        """
        self.regression_detector = regression_detector or RegressionDetector()
        self.comparisons: Dict[str, CrossVersionComparison] = {}
        self.provider_analyses: Dict[str, List[ProviderVersionAnalysis]] = {}

    def compare_versions(
        self,
        baseline_traces: List[Dict],
        comparison_traces: List[Dict],
        baseline_version: str,
        comparison_version: str,
        comparison_id: str,
    ) -> CrossVersionComparison:
        """
        Compare two versions of traces.

        Args:
            baseline_traces: List of baseline traces
            comparison_traces: List of comparison traces
            baseline_version: Baseline version identifier
            comparison_version: Comparison version identifier
            comparison_id: Unique comparison identifier

        Returns:
            CrossVersionComparison report
        """
        comparison = CrossVersionComparison(
            comparison_id=comparison_id,
            timestamp=datetime.now(timezone.utc),
            baseline_version=baseline_version,
            comparison_version=comparison_version,
            baseline_traces=len(baseline_traces),
            comparison_traces=len(comparison_traces),
        )

        # Match traces for comparison
        matched_pairs = self._match_traces(baseline_traces, comparison_traces)
        comparison.comparable_traces = len(matched_pairs)

        # Analyze each matched pair
        regressions = []
        improvements = []

        for baseline, comparison_trace in matched_pairs:
            # Detect regression
            event_id = f"{comparison_id}_{baseline.get('trace_id', 'unknown')}"
            regression = self.regression_detector.detect_regression(
                baseline,
                comparison_trace,
                baseline_version,
                comparison_version,
                event_id,
            )

            if regression:
                regressions.append(regression)
                # Update stats
                if regression.regression_type != RegressionType.UNKNOWN:
                    comparison.total_regressions += 1
                    if regression.severity == RegressionSeverity.CRITICAL:
                        comparison.critical_regressions += 1
                    elif regression.severity == RegressionSeverity.HIGH:
                        comparison.high_regressions += 1
                    elif regression.severity == RegressionSeverity.MEDIUM:
                        comparison.medium_regressions += 1
                    elif regression.severity == RegressionSeverity.LOW:
                        comparison.low_regressions += 1

                    # Update provider stats
                    provider = baseline.get("provider", "unknown")
                    if provider not in comparison.provider_regressions:
                        comparison.provider_regressions[provider] = 0
                    comparison.provider_regressions[provider] += 1

                    # Update domain stats
                    domain = baseline.get("domain", "unknown")
                    if domain not in comparison.domain_regressions:
                        comparison.domain_regressions[domain] = 0
                    comparison.domain_regressions[domain] += 1
            else:
                # Check for improvements
                if (
                    comparison_trace.get("quality_score", 0)
                    > baseline.get("quality_score", 0) * 1.05
                    or comparison_trace.get("token_efficiency", 0)
                    > baseline.get("token_efficiency", 0) * 1.05
                ):
                    improvements.append((baseline, comparison_trace))
                    comparison.total_improvements += 1

                    if comparison_trace.get("quality_score", 0) > baseline.get(
                        "quality_score", 0
                    ):
                        comparison.quality_improvements += 1
                    if comparison_trace.get("total_duration_ms", 0) < baseline.get(
                        "total_duration_ms", 0
                    ):
                        comparison.latency_improvements += 1
                    if comparison_trace.get("token_efficiency", 0) > baseline.get(
                        "token_efficiency", 0
                    ):
                        comparison.token_improvements += 1

        # Calculate averages
        if comparison.comparable_traces > 0:
            quality_deltas = [
                comparison_trace.get("quality_score", 0)
                - baseline.get("quality_score", 0)
                for baseline, comparison_trace in matched_pairs
            ]
            comparison.average_quality_delta = sum(quality_deltas) / len(quality_deltas)

            semantic_deltas = [
                comparison_trace.get("semantic_retention", 0)
                - baseline.get("semantic_retention", 0)
                for baseline, comparison_trace in matched_pairs
            ]
            comparison.average_semantic_delta = sum(semantic_deltas) / len(
                semantic_deltas
            )

            token_deltas = [
                comparison_trace.get("token_efficiency", 0)
                - baseline.get("token_efficiency", 0)
                for baseline, comparison_trace in matched_pairs
            ]
            comparison.average_token_efficiency_delta = sum(token_deltas) / len(
                token_deltas
            )

            latency_deltas = [
                comparison_trace.get("total_duration_ms", 0)
                - baseline.get("total_duration_ms", 0)
                for baseline, comparison_trace in matched_pairs
            ]
            comparison.average_latency_delta_ms = sum(latency_deltas) / len(
                latency_deltas
            )

        # Find most affected provider
        if comparison.provider_regressions:
            comparison.most_affected_provider = max(
                comparison.provider_regressions.items(), key=lambda x: x[1]
            )[0]

        # Generate overall verdict
        self._generate_verdict(comparison)

        self.comparisons[comparison_id] = comparison
        return comparison

    def analyze_provider_versions(
        self,
        baseline_traces: List[Dict],
        comparison_traces: List[Dict],
        baseline_version: str,
        comparison_version: str,
    ) -> List[ProviderVersionAnalysis]:
        """
        Build provider-by-provider evolution report across two versions.
        """
        providers = sorted(
            set([t.get("provider", "unknown") for t in baseline_traces]).union(
                set([t.get("provider", "unknown") for t in comparison_traces])
            )
        )

        analyses: List[ProviderVersionAnalysis] = []
        for provider in providers:
            baseline_provider = [
                t for t in baseline_traces if t.get("provider", "unknown") == provider
            ]
            comparison_provider = [
                t
                for t in comparison_traces
                if t.get("provider", "unknown") == provider
            ]
            if not baseline_provider or not comparison_provider:
                continue

            baseline_quality_values = [
                float(t.get("quality_score", 0.0)) for t in baseline_provider
            ]
            comparison_quality_values = [
                float(t.get("quality_score", 0.0)) for t in comparison_provider
            ]
            baseline_latency_values = [
                float(t.get("total_duration_ms", 0.0)) for t in baseline_provider
            ]
            comparison_latency_values = [
                float(t.get("total_duration_ms", 0.0)) for t in comparison_provider
            ]
            baseline_token_values = [
                float(t.get("token_efficiency", 0.0)) for t in baseline_provider
            ]
            comparison_token_values = [
                float(t.get("token_efficiency", 0.0)) for t in comparison_provider
            ]

            baseline_avg_quality = sum(baseline_quality_values) / len(
                baseline_quality_values
            )
            comparison_avg_quality = sum(comparison_quality_values) / len(
                comparison_quality_values
            )
            baseline_avg_latency = sum(baseline_latency_values) / len(
                baseline_latency_values
            )
            comparison_avg_latency = sum(comparison_latency_values) / len(
                comparison_latency_values
            )
            baseline_avg_token = sum(baseline_token_values) / len(
                baseline_token_values
            )
            comparison_avg_token = sum(comparison_token_values) / len(
                comparison_token_values
            )

            analysis = ProviderVersionAnalysis(
                provider=provider,
                baseline_version=baseline_version,
                comparison_version=comparison_version,
                baseline_traces=len(baseline_provider),
                comparison_traces=len(comparison_provider),
                baseline_avg_quality=baseline_avg_quality,
                comparison_avg_quality=comparison_avg_quality,
                quality_delta=round(comparison_avg_quality - baseline_avg_quality, 10),
                baseline_quality_variance=self._variance(baseline_quality_values),
                comparison_quality_variance=self._variance(comparison_quality_values),
                baseline_avg_latency_ms=baseline_avg_latency,
                comparison_avg_latency_ms=comparison_avg_latency,
                latency_delta=round(comparison_avg_latency - baseline_avg_latency, 10),
                baseline_avg_token_efficiency=baseline_avg_token,
                comparison_avg_token_efficiency=comparison_avg_token,
                token_efficiency_delta=round(
                    comparison_avg_token - baseline_avg_token, 10
                ),
            )

            analysis.stability_change = round(
                analysis.baseline_quality_variance
                - analysis.comparison_quality_variance,
                10,
            )
            analysis.regressions = sum(
                1
                for event in self.regression_detector.detected_regressions
                if event.provider == provider
                and event.baseline_version == baseline_version
                and event.comparison_version == comparison_version
            )

            matched_pairs = self._match_traces(baseline_provider, comparison_provider)
            analysis.improvements = sum(
                1
                for baseline, current in matched_pairs
                if current.get("quality_score", 0.0) > baseline.get("quality_score", 0.0)
                or current.get("token_efficiency", 0.0)
                > baseline.get("token_efficiency", 0.0)
                or current.get("total_duration_ms", 0.0)
                < baseline.get("total_duration_ms", 0.0)
            )

            if analysis.quality_delta < -0.05:
                analysis.status_change = "degraded"
            elif analysis.quality_delta > 0.05:
                analysis.status_change = "improved"
            else:
                analysis.status_change = "stable"

            analyses.append(analysis)

        history_key = f"{baseline_version}->{comparison_version}"
        self.provider_analyses[history_key] = analyses
        return analyses

    def _variance(self, values: List[float]) -> float:
        """Calculate variance for a list."""
        if len(values) < 2:
            return 0.0
        mean_val = sum(values) / len(values)
        return sum((value - mean_val) ** 2 for value in values) / len(values)

    def _match_traces(
        self,
        baseline_traces: List[Dict],
        comparison_traces: List[Dict],
    ) -> List[Tuple[Dict, Dict]]:
        """
        Match traces between versions for comparison.

        Uses query, provider, and compression mode as matching keys.
        """
        matched_pairs = []

        # Create lookup by key
        comparison_lookup = {}
        for trace in comparison_traces:
            key = (
                trace.get("query", ""),
                trace.get("provider", ""),
                trace.get("compression_mode", ""),
            )
            if key not in comparison_lookup:
                comparison_lookup[key] = []
            comparison_lookup[key].append(trace)

        # Match baseline traces
        for baseline in baseline_traces:
            key = (
                baseline.get("query", ""),
                baseline.get("provider", ""),
                baseline.get("compression_mode", ""),
            )
            if key in comparison_lookup and comparison_lookup[key]:
                # Find best match (most similar memory count)
                comparison_trace = min(
                    comparison_lookup[key],
                    key=lambda t: abs(
                        t.get("memories_count", 0) - baseline.get("memories_count", 0)
                    ),
                )
                matched_pairs.append((baseline, comparison_trace))
                comparison_lookup[key].remove(comparison_trace)

        return matched_pairs

    def _generate_verdict(self, comparison: CrossVersionComparison) -> None:
        """Generate overall verdict for the comparison."""
        total_traces = comparison.comparable_traces
        if total_traces == 0:
            comparison.is_regression_overall = False
            comparison.recommendation = "No comparable traces found"
            return

        regression_ratio = comparison.total_regressions / total_traces
        improvement_ratio = comparison.total_improvements / total_traces

        # Calculate confidence
        critical_weight = comparison.critical_regressions * 5
        high_weight = comparison.high_regressions * 3
        medium_weight = comparison.medium_regressions * 1.5

        total_regression_weight = critical_weight + high_weight + medium_weight
        comparison.regression_confidence = min(
            total_regression_weight / max(total_traces, 1) / 5, 1.0
        )

        # Determine overall status
        if regression_ratio > 0.3 and regression_ratio > improvement_ratio:
            comparison.is_regression_overall = True
            if comparison.critical_regressions > 0:
                comparison.recommendation = "REJECT: Critical regressions detected. Investigate root causes before merge."
            elif regression_ratio > 0.5:
                comparison.recommendation = (
                    "CAUTION: High regression rate. Review changes carefully."
                )
            else:
                comparison.recommendation = (
                    "INVESTIGATE: Moderate regressions detected. Analyze trade-offs."
                )
        elif improvement_ratio > regression_ratio * 2:
            comparison.is_regression_overall = False
            comparison.recommendation = (
                "APPROVED: Significant improvements detected. Safe to merge."
            )
        else:
            comparison.is_regression_overall = False
            comparison.recommendation = (
                "NEUTRAL: Mixed results. Standard review recommended."
            )


class RegressionHistoryTracker:
    """
    Tracks regression history and trends across multiple versions.

    Provides:
    - Historical regression tracking
    - Trend analysis and regression patterns
    - Version progression analysis
    - Regression severity trends
    """

    def __init__(self):
        """Initialize history tracker."""
        self.regression_history: List[RegressionEvent] = []
        self.comparison_history: List[CrossVersionComparison] = []
        self.version_timeline: List[str] = []

    def record_regression(self, event: RegressionEvent) -> None:
        """Record a regression event."""
        self.regression_history.append(event)

        # Update version timeline
        if event.comparison_version not in self.version_timeline:
            self.version_timeline.append(event.comparison_version)

    def record_comparison(self, comparison: CrossVersionComparison) -> None:
        """Record a comparison result."""
        self.comparison_history.append(comparison)
        if comparison.baseline_version not in self.version_timeline:
            self.version_timeline.append(comparison.baseline_version)
        if comparison.comparison_version not in self.version_timeline:
            self.version_timeline.append(comparison.comparison_version)

    def get_regression_trends(self) -> Dict[str, Any]:
        """Analyze regression trends."""
        if not self.regression_history:
            return {"total_regressions": 0, "trends": []}

        # Group by type
        by_type = {}
        for event in self.regression_history:
            rtype = event.regression_type.value
            if rtype not in by_type:
                by_type[rtype] = []
            by_type[rtype].append(event)

        # Group by severity
        by_severity = {}
        for event in self.regression_history:
            severity = event.severity.name
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(event)

        return {
            "total_regressions": len(self.regression_history),
            "by_type": self._build_type_summary(by_type),
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "most_common_type": max(by_type.items(), key=lambda x: len(x[1]))[0]
            if by_type
            else None,
            "most_severe_regression": max(
                (e for e in self.regression_history),
                key=lambda e: e.severity.value,
                default=None,
            ).to_dict()
            if self.regression_history
            else None,
        }

    def get_version_progression(self) -> Dict[str, Any]:
        """Analyze version progression."""
        if not self.comparison_history:
            return {"versions": [], "progression": []}

        progression = []
        for comparison in self.comparison_history:
            progression.append(
                {
                    "from": comparison.baseline_version,
                    "to": comparison.comparison_version,
                    "regressions": comparison.total_regressions,
                    "improvements": comparison.total_improvements,
                    "verdict": "REGRESSION"
                    if comparison.is_regression_overall
                    else "OK",
                }
            )

        return {
            "versions": self.version_timeline,
            "progression": progression,
            "total_comparisons": len(self.comparison_history),
        }

    def get_provider_regression_summary(self) -> Dict[str, int]:
        """Get regression count by provider."""
        by_provider = {}
        for event in self.regression_history:
            provider = event.provider or "unknown"
            by_provider[provider] = by_provider.get(provider, 0) + 1
        return by_provider

    def get_critical_regressions(self) -> List[RegressionEvent]:
        """Get all critical regressions."""
        return [
            e
            for e in self.regression_history
            if e.severity == RegressionSeverity.CRITICAL
        ]

    def export_history(self, output_file: str) -> str:
        """Persist regression/comparison history to JSON."""
        report = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "versions": self.version_timeline,
            "regressions": [event.to_dict() for event in self.regression_history],
            "comparisons": [cmp.to_dict() for cmp in self.comparison_history],
            "trends": self.get_regression_trends(),
            "progression": self.get_version_progression(),
        }

        with open(output_file, "w") as file_obj:
            json.dump(report, file_obj, indent=2)

        logger.info(f"Regression history exported to {output_file}")
        return output_file

    def load_history(self, input_file: str) -> None:
        """Load regression/comparison history from JSON."""
        with open(input_file, "r") as file_obj:
            data = json.load(file_obj)

        self.version_timeline = list(data.get("versions", []))
        self.regression_history = [
            RegressionEvent.from_dict(event) for event in data.get("regressions", [])
        ]
        self.comparison_history = [
            CrossVersionComparison.from_dict(cmp)
            for cmp in data.get("comparisons", [])
        ]

        logger.info(f"Loaded regression history from {input_file}")

    def _build_type_summary(self, by_type: Dict[str, List[RegressionEvent]]) -> Dict[str, int]:
        """
        Build type summary with lowercase canonical keys and uppercase aliases.

        Preserves current behavior while keeping backward compatibility for
        callers expecting enum-name style keys.
        """
        summary: Dict[str, int] = {}
        for reg_type, events in by_type.items():
            count = len(events)
            summary[reg_type] = count
            summary[reg_type.upper()] = count
        return summary
