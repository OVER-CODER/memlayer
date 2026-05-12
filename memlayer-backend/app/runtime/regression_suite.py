"""
Regression Replay & Comparison orchestration for Phase 5B.

Builds deterministic cross-version regression intelligence on top of:
- CrossVersionComparator
- RegressionHistoryTracker
- RuntimeReplayEngine
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
import copy
import hashlib
import json
import logging
import uuid

from app.runtime.regression_comparison import (
    CrossVersionComparator,
    RegressionHistoryTracker,
    CrossVersionComparison,
    ProviderVersionAnalysis,
    RegressionEvent,
)
from app.runtime.replay_engine import RuntimeReplayEngine, get_replay_engine

logger = logging.getLogger(__name__)


@dataclass
class VersionedTraceSet:
    """Deterministic trace set for a compiler/runtime version."""

    version: str
    traces: List[Dict[str, Any]]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    checksum: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def calculate_checksum(self) -> str:
        """Compute stable checksum for trace set integrity."""
        canonical = json.dumps(self.traces, sort_keys=True, default=str)
        self.checksum = hashlib.sha256(canonical.encode()).hexdigest()[:24]
        return self.checksum

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "checksum": self.checksum,
            "metadata": self.metadata,
            "trace_count": len(self.traces),
            "traces": self.traces,
        }


@dataclass
class RegressionReplayReport:
    """Full cross-version regression report."""

    report_id: str
    baseline_version: str
    comparison_version: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    comparison: Optional[CrossVersionComparison] = None
    provider_analysis: List[ProviderVersionAnalysis] = field(default_factory=list)
    regression_events: List[RegressionEvent] = field(default_factory=list)

    replay_delta_summary: Dict[str, Any] = field(default_factory=dict)
    optimization_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp.isoformat(),
            "baseline_version": self.baseline_version,
            "comparison_version": self.comparison_version,
            "comparison": self.comparison.to_dict() if self.comparison else None,
            "provider_analysis": [entry.to_dict() for entry in self.provider_analysis],
            "regression_events": [event.to_dict() for event in self.regression_events],
            "replay_delta_summary": self.replay_delta_summary,
            "optimization_summary": self.optimization_summary,
        }


class RegressionReplaySuite:
    """
    Deterministic regression + replay comparison suite for runtime validation.
    """

    def __init__(
        self,
        comparator: Optional[CrossVersionComparator] = None,
        history_tracker: Optional[RegressionHistoryTracker] = None,
        replay_engine: Optional[RuntimeReplayEngine] = None,
        max_reports: int = 1000,
    ):
        self.comparator = comparator or CrossVersionComparator()
        self.history_tracker = history_tracker or RegressionHistoryTracker()
        self.replay_engine = replay_engine or get_replay_engine()
        self.max_reports = max_reports

        self.versioned_traces: Dict[str, VersionedTraceSet] = {}
        self.reports: List[RegressionReplayReport] = []

    def register_version_traces(
        self,
        version: str,
        traces: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VersionedTraceSet:
        """Register deterministic trace snapshot for a specific version."""
        stable_traces = copy.deepcopy(traces)
        trace_set = VersionedTraceSet(
            version=version,
            traces=stable_traces,
            metadata=metadata or {},
        )
        trace_set.calculate_checksum()
        self.versioned_traces[version] = trace_set
        return trace_set

    def register_version_from_replay_engine(
        self,
        version: str,
        provider: Optional[str] = None,
        compression_mode: Optional[str] = None,
        query_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VersionedTraceSet:
        """Register traces directly from the replay engine."""
        replayable = self.replay_engine.list_traces(
            provider=provider,
            compression_mode=compression_mode,
            query_type=query_type,
        )
        traces = [self._replayable_to_comparison_trace(trace) for trace in replayable]
        trace_set = self.register_version_traces(version=version, traces=traces, metadata=metadata)
        logger.info(
            f"Registered {len(traces)} traces from replay engine for version {version}"
        )
        return trace_set

    def compare_versions(
        self,
        baseline_version: str,
        comparison_version: str,
        report_id: Optional[str] = None,
    ) -> RegressionReplayReport:
        """Run full deterministic cross-version regression analysis."""
        baseline_set = self.versioned_traces.get(baseline_version)
        comparison_set = self.versioned_traces.get(comparison_version)
        if not baseline_set or not comparison_set:
            raise ValueError("Both baseline and comparison versions must be registered")

        comparison_id = report_id or f"cmp-{uuid.uuid4().hex[:10]}"
        comparison = self.comparator.compare_versions(
            baseline_traces=baseline_set.traces,
            comparison_traces=comparison_set.traces,
            baseline_version=baseline_version,
            comparison_version=comparison_version,
            comparison_id=comparison_id,
        )

        provider_analysis = self.comparator.analyze_provider_versions(
            baseline_traces=baseline_set.traces,
            comparison_traces=comparison_set.traces,
            baseline_version=baseline_version,
            comparison_version=comparison_version,
        )

        regression_events = [
            event
            for event in self.comparator.regression_detector.detected_regressions
            if event.baseline_version == baseline_version
            and event.comparison_version == comparison_version
            and event.event_id.startswith(comparison_id)
        ]

        for event in regression_events:
            self.history_tracker.record_regression(event)
        self.history_tracker.record_comparison(comparison)

        replay_delta_summary = self._build_replay_delta_summary(
            baseline_set.traces,
            comparison_set.traces,
        )
        optimization_summary = self._build_optimization_summary(comparison)

        report = RegressionReplayReport(
            report_id=comparison_id,
            baseline_version=baseline_version,
            comparison_version=comparison_version,
            comparison=comparison,
            provider_analysis=provider_analysis,
            regression_events=regression_events,
            replay_delta_summary=replay_delta_summary,
            optimization_summary=optimization_summary,
        )

        self.reports.append(report)
        if len(self.reports) > self.max_reports:
            self.reports = self.reports[-self.max_reports :]

        logger.info(
            f"Generated regression report {comparison_id} ({baseline_version} -> {comparison_version})"
        )
        return report

    def get_report(self, report_id: str) -> Optional[RegressionReplayReport]:
        """Fetch specific report by ID."""
        for report in self.reports:
            if report.report_id == report_id:
                return report
        return None

    def list_reports(self, limit: int = 100) -> List[RegressionReplayReport]:
        """List recent reports."""
        return self.reports[-limit:]

    def export_report(self, report_id: str, output_file: str) -> str:
        """Export one report to JSON."""
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Report not found: {report_id}")

        payload = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "report": report.to_dict(),
        }
        with open(output_file, "w") as file_obj:
            json.dump(payload, file_obj, indent=2)

        logger.info(f"Exported regression report {report_id} to {output_file}")
        return output_file

    def export_suite_history(self, output_file: str) -> str:
        """Export all registered versions and reports to JSON."""
        payload = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "versions": {
                version: trace_set.to_dict()
                for version, trace_set in self.versioned_traces.items()
            },
            "reports": [report.to_dict() for report in self.reports],
            "regression_history": self.history_tracker.get_regression_trends(),
            "version_progression": self.history_tracker.get_version_progression(),
        }
        with open(output_file, "w") as file_obj:
            json.dump(payload, file_obj, indent=2)

        logger.info(f"Exported regression suite history to {output_file}")
        return output_file

    def _replayable_to_comparison_trace(self, trace: Any) -> Dict[str, Any]:
        """Normalize replay trace to comparator shape."""
        return {
            "trace_id": trace.trace_id,
            "query": trace.query,
            "query_type": trace.query_type,
            "provider": trace.provider,
            "compression_mode": trace.compression_mode,
            "token_budget": trace.token_budget,
            "memories_count": trace.memories_count,
            "quality_score": trace.quality_score,
            "semantic_retention": trace.semantic_retention,
            "token_efficiency": trace.token_efficiency,
            "total_duration_ms": trace.total_duration_ms,
            "token_metrics": trace.token_metrics,
        }

    def _build_replay_delta_summary(
        self,
        baseline_traces: List[Dict[str, Any]],
        comparison_traces: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Compute deterministic deltas between matched traces.
        """
        pairs = self.comparator._match_traces(baseline_traces, comparison_traces)
        if not pairs:
            return {"matched_traces": 0, "deltas": []}

        deltas = []
        quality_regressions = 0
        semantic_regressions = 0
        latency_regressions = 0
        for baseline, current in pairs:
            quality_delta = round(
                float(current.get("quality_score", 0.0))
                - float(baseline.get("quality_score", 0.0)),
                10,
            )
            semantic_delta = round(
                float(current.get("semantic_retention", 0.0))
                - float(baseline.get("semantic_retention", 0.0)),
                10,
            )
            token_delta = round(
                float(current.get("token_efficiency", 0.0))
                - float(baseline.get("token_efficiency", 0.0)),
                10,
            )
            latency_delta = round(
                float(current.get("total_duration_ms", 0.0))
                - float(baseline.get("total_duration_ms", 0.0)),
                10,
            )
            if quality_delta < 0:
                quality_regressions += 1
            if semantic_delta < 0:
                semantic_regressions += 1
            if latency_delta > 0:
                latency_regressions += 1

            deltas.append(
                {
                    "baseline_trace_id": baseline.get("trace_id", ""),
                    "comparison_trace_id": current.get("trace_id", ""),
                    "query": baseline.get("query", ""),
                    "provider": baseline.get("provider", ""),
                    "quality_delta": quality_delta,
                    "semantic_delta": semantic_delta,
                    "token_efficiency_delta": token_delta,
                    "latency_delta_ms": latency_delta,
                }
            )

        return {
            "matched_traces": len(pairs),
            "quality_regressions": quality_regressions,
            "semantic_regressions": semantic_regressions,
            "latency_regressions": latency_regressions,
            "deltas": deltas,
        }

    def _build_optimization_summary(
        self, comparison: CrossVersionComparison
    ) -> Dict[str, Any]:
        """Build optimization impact summary from comparison result."""
        return {
            "overall_status": "regression"
            if comparison.is_regression_overall
            else "stable_or_improved",
            "quality_impact": comparison.average_quality_delta,
            "semantic_impact": comparison.average_semantic_delta,
            "token_efficiency_impact": comparison.average_token_efficiency_delta,
            "latency_impact_ms": comparison.average_latency_delta_ms,
            "regressions": comparison.total_regressions,
            "improvements": comparison.total_improvements,
            "regression_confidence": comparison.regression_confidence,
            "recommendation": comparison.recommendation,
        }
