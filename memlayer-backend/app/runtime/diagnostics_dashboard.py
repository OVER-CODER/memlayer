"""
Runtime Diagnostics Dashboard for Phase 5B.

Developer-focused semantic runtime profiler that aggregates telemetry and
runtime subsystems into dashboard-ready diagnostics snapshots.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

from app.runtime.integrated_runtime import IntegratedRuntimeSystem
from app.runtime.replay_engine import RuntimeReplayEngine, get_replay_engine
from app.runtime.failure_detector import EmergentFailureDetector, get_failure_detector
from app.runtime.evolution_tracker import RuntimeEvolutionTracker, get_evolution_tracker
from app.runtime.stress_harness import LongHorizonStressHarness
from app.telemetry import (
    RuntimeTraceService,
    TokenAnalyticsService,
    LatencyProfiler,
    SemanticDriftAnalyzer,
    ProviderBenchmarkingService,
    get_trace_service,
    get_token_analytics,
    get_latency_profiler,
    get_drift_analyzer,
    get_benchmarking_service,
)

logger = logging.getLogger(__name__)


@dataclass
class RuntimeDiagnosticsSnapshot:
    """Serializable diagnostics snapshot."""

    snapshot_id: str
    generated_at: datetime = field(default_factory=datetime.utcnow)
    runtime_overview: Dict[str, Any] = field(default_factory=dict)
    replay_diagnostics: Dict[str, Any] = field(default_factory=dict)
    token_evolution: Dict[str, Any] = field(default_factory=dict)
    semantic_drift_timeline: Dict[str, Any] = field(default_factory=dict)
    runtime_evolution: Dict[str, Any] = field(default_factory=dict)
    provider_adaptation: Dict[str, Any] = field(default_factory=dict)
    latency_diagnostics: Dict[str, Any] = field(default_factory=dict)
    failure_propagation: Dict[str, Any] = field(default_factory=dict)
    context_evolution_timeline: List[Dict[str, Any]] = field(default_factory=list)
    stress_validation: Dict[str, Any] = field(default_factory=dict)
    cognition_stability: Dict[str, Any] = field(default_factory=dict)
    view_engine_diagnostics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "snapshot_id": self.snapshot_id,
            "generated_at": self.generated_at.isoformat(),
            "runtime_overview": self.runtime_overview,
            "replay_diagnostics": self.replay_diagnostics,
            "token_evolution": self.token_evolution,
            "semantic_drift_timeline": self.semantic_drift_timeline,
            "runtime_evolution": self.runtime_evolution,
            "provider_adaptation": self.provider_adaptation,
            "latency_diagnostics": self.latency_diagnostics,
            "failure_propagation": self.failure_propagation,
            "context_evolution_timeline": self.context_evolution_timeline,
            "stress_validation": self.stress_validation,
            "cognition_stability": self.cognition_stability,
            "view_engine_diagnostics": self.view_engine_diagnostics,
        }


class RuntimeDiagnosticsDashboard:
    """
    Aggregates runtime observability data into diagnostics dashboard snapshots.
    """

    def __init__(
        self,
        integrated_runtime: Optional[IntegratedRuntimeSystem] = None,
        trace_service: Optional[RuntimeTraceService] = None,
        token_analytics: Optional[TokenAnalyticsService] = None,
        latency_profiler: Optional[LatencyProfiler] = None,
        drift_analyzer: Optional[SemanticDriftAnalyzer] = None,
        benchmarking_service: Optional[ProviderBenchmarkingService] = None,
        replay_engine: Optional[RuntimeReplayEngine] = None,
        failure_detector: Optional[EmergentFailureDetector] = None,
        evolution_tracker: Optional[RuntimeEvolutionTracker] = None,
        stress_harness: Optional[LongHorizonStressHarness] = None,
        view_diagnostics_dashboard: Optional[Any] = None,
    ):
        self.integrated_runtime = integrated_runtime
        self.trace_service = trace_service or get_trace_service()
        self.token_analytics = token_analytics or get_token_analytics()
        self.latency_profiler = latency_profiler or get_latency_profiler()
        self.drift_analyzer = drift_analyzer or get_drift_analyzer()
        self.benchmarking_service = benchmarking_service or get_benchmarking_service()
        self.replay_engine = replay_engine or get_replay_engine()
        self.failure_detector = failure_detector or get_failure_detector()
        self.evolution_tracker = evolution_tracker or get_evolution_tracker()
        self.stress_harness = stress_harness
        self.view_diagnostics_dashboard = view_diagnostics_dashboard
        self.snapshots: List[RuntimeDiagnosticsSnapshot] = []

    def capture_snapshot(
        self,
        snapshot_id: Optional[str] = None,
        lookback_traces: int = 200,
        trend_hours: int = 24,
    ) -> RuntimeDiagnosticsSnapshot:
        """Capture current end-to-end runtime diagnostics state."""
        resolved_snapshot_id = snapshot_id or f"diag-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        snapshot = RuntimeDiagnosticsSnapshot(snapshot_id=resolved_snapshot_id)

        snapshot.runtime_overview = self._build_runtime_overview()
        snapshot.replay_diagnostics = self._build_replay_diagnostics()
        snapshot.token_evolution = self._build_token_evolution(trend_hours=trend_hours)
        snapshot.semantic_drift_timeline = self._build_semantic_drift_timeline(
            trend_hours=trend_hours
        )
        snapshot.runtime_evolution = self.evolution_tracker.get_summary()
        snapshot.provider_adaptation = self._build_provider_adaptation()
        snapshot.latency_diagnostics = self._build_latency_diagnostics(
            trend_hours=trend_hours
        )
        snapshot.failure_propagation = self._build_failure_propagation()
        snapshot.context_evolution_timeline = self._build_context_timeline(
            lookback_traces=lookback_traces
        )
        snapshot.stress_validation = self._build_stress_validation()
        snapshot.cognition_stability = self._build_cognition_stability(snapshot)
        snapshot.view_engine_diagnostics = self._build_view_engine_diagnostics()

        self.snapshots.append(snapshot)
        return snapshot

    def render_console_report(self, snapshot: RuntimeDiagnosticsSnapshot) -> str:
        """Render diagnostics snapshot as a profiler-style text report."""
        runtime = snapshot.runtime_overview
        replay = snapshot.replay_diagnostics
        failure = snapshot.failure_propagation
        stability = snapshot.cognition_stability

        lines = [
            "=" * 88,
            "MEMLAYER RUNTIME DIAGNOSTICS CONSOLE",
            "=" * 88,
            f"Snapshot: {snapshot.snapshot_id}",
            f"Generated: {snapshot.generated_at.isoformat()}",
            "",
            "[Runtime Overview]",
            f"Executions: {runtime.get('total_executions', 0)}",
            f"Success Rate: {runtime.get('success_rate', 0.0):.2%}",
            f"Avg Quality: {runtime.get('avg_quality_score', 0.0):.3f}",
            f"Avg Semantic Retention: {runtime.get('avg_semantic_retention', 0.0):.3f}",
            f"Avg Token Efficiency: {runtime.get('avg_token_efficiency', 0.0):.3f}",
            f"Avg Duration (ms): {runtime.get('avg_duration_ms', 0.0):.2f}",
            "",
            "[Replay & Regression]",
            f"Stored Traces: {replay.get('stored_traces', 0)}",
            f"Replay Success Rate: {replay.get('success_rate', 0.0):.2%}",
            f"Average Fidelity: {replay.get('avg_fidelity_score', 0.0):.2f}",
            f"Regressions Detected: {replay.get('regressions_detected', 0)}",
            "",
            "[Failure Propagation]",
            f"Total Failures: {failure.get('total_failures', 0)}",
            f"Critical+ Errors: {failure.get('critical_or_higher', 0)}",
            f"Most Frequent Failure: {failure.get('most_frequent_failure_type', 'none')}",
            "",
            "[Cognition Stability]",
            f"Stability Score: {stability.get('stability_score', 0.0):.2f}",
            f"Stability Class: {stability.get('stability_classification', 'unknown')}",
            f"Failure Pressure: {stability.get('failure_pressure', 0.0):.3f}",
            "",
            "[View Engine]",
            f"View Snapshot: {snapshot.view_engine_diagnostics.get('snapshot_id', 'none')}",
            f"Views Compiled: {snapshot.view_engine_diagnostics.get('total_views_compiled', 0)}",
            (
                "View Avg Quality: "
                f"{snapshot.view_engine_diagnostics.get('avg_view_quality', 0.0):.3f}"
            ),
            "=" * 88,
        ]
        return "\n".join(lines)

    def export_snapshot(self, snapshot: RuntimeDiagnosticsSnapshot, output_file: str) -> str:
        """Export snapshot as JSON."""
        payload = {
            "exported_at": datetime.utcnow().isoformat(),
            "snapshot": snapshot.to_dict(),
        }
        with open(output_file, "w") as file_obj:
            json.dump(payload, file_obj, indent=2)
        logger.info(f"Exported diagnostics snapshot to {output_file}")
        return output_file

    def export_console_report(
        self, snapshot: RuntimeDiagnosticsSnapshot, output_file: str
    ) -> str:
        """Export console diagnostics report to text file."""
        with open(output_file, "w") as file_obj:
            file_obj.write(self.render_console_report(snapshot))
        logger.info(f"Exported diagnostics console report to {output_file}")
        return output_file

    def _build_runtime_overview(self) -> Dict[str, Any]:
        if self.integrated_runtime is None:
            return {"message": "Integrated runtime not attached"}
        return self.integrated_runtime.get_runtime_statistics()

    def _build_replay_diagnostics(self) -> Dict[str, Any]:
        stats = self.replay_engine.get_replay_statistics()
        recent_results = [result.to_dict() for result in self.replay_engine.replay_results[-25:]]
        return {
            **stats,
            "recent_replays": recent_results,
        }

    def _build_token_evolution(self, trend_hours: int) -> Dict[str, Any]:
        return {
            "analytics_report": self.token_analytics.get_analytics_report(),
            "compression_ratio_trend": self.token_analytics.get_historical_trend(
                metric_name="compression_ratio",
                hours=trend_hours,
            ),
            "efficiency_trend": self.token_analytics.get_historical_trend(
                metric_name="efficiency",
                hours=trend_hours,
            ),
            "semantic_density_trend": self.token_analytics.get_historical_trend(
                metric_name="semantic_density",
                hours=trend_hours,
            ),
            "tokens_saved_trend": self.token_analytics.get_historical_trend(
                metric_name="tokens_saved",
                hours=trend_hours,
            ),
        }

    def _build_semantic_drift_timeline(self, trend_hours: int) -> Dict[str, Any]:
        return {
            "drift_report": self.drift_analyzer.get_drift_analyzer_report(),
            "drift_trends": self.drift_analyzer.get_drift_trends(hours=trend_hours),
        }

    def _build_provider_adaptation(self) -> Dict[str, Any]:
        return {
            "benchmark_report": self.benchmarking_service.get_benchmarking_report(),
            "latency_provider_comparison": self.latency_profiler.get_provider_comparison(),
            "token_provider_comparison": self.token_analytics.get_provider_comparison(),
            "drift_provider_comparison": self.drift_analyzer.get_provider_drift_comparison(),
        }

    def _build_latency_diagnostics(self, trend_hours: int) -> Dict[str, Any]:
        return {
            "profiler_report": self.latency_profiler.get_profiler_report(),
            "latency_heatmap": self.latency_profiler.get_latency_heatmap(
                hours=trend_hours
            ),
        }

    def _build_failure_propagation(self) -> Dict[str, Any]:
        base_report = self.failure_detector.get_failure_report()
        if "message" in base_report:
            return {
                "total_failures": 0,
                "critical_or_higher": 0,
                "most_frequent_failure_type": "none",
                "report": base_report,
            }

        by_type = base_report.get("by_type", {})
        by_severity = base_report.get("by_severity", {})
        critical_or_higher = (
            by_severity.get("critical", 0) + by_severity.get("catastrophic", 0)
        )
        most_frequent_failure_type = (
            max(by_type.items(), key=lambda item: item[1])[0] if by_type else "none"
        )
        return {
            "total_failures": base_report.get("total_failures", 0),
            "critical_or_higher": critical_or_higher,
            "most_frequent_failure_type": most_frequent_failure_type,
            "report": base_report,
        }

    def _build_context_timeline(self, lookback_traces: int) -> List[Dict[str, Any]]:
        traces = self.trace_service.get_recent_traces(limit=lookback_traces)
        return [
            {
                "trace_id": trace.trace_id,
                "started_at": trace.started_at.isoformat(),
                "duration_ms": trace.total_duration_ms,
                "quality_score": trace.overall_quality_score,
                "semantic_retention": trace.semantic_retention,
                "token_savings": trace.total_token_savings,
                "provider": trace.provider,
                "compression_mode": trace.compression_mode,
                "success": trace.success,
                "stage_breakdown": trace.stage_breakdown,
            }
            for trace in traces
        ]

    def _build_stress_validation(self) -> Dict[str, Any]:
        if self.stress_harness is None:
            return {"message": "Stress harness not attached"}
        return self.stress_harness.get_stress_report()

    def _build_view_engine_diagnostics(self) -> Dict[str, Any]:
        """Attach optional Phase 6 view diagnostics into runtime snapshot."""
        if self.view_diagnostics_dashboard is None:
            return {"message": "View diagnostics not attached"}

        snapshot = self.view_diagnostics_dashboard.capture_snapshot()
        if hasattr(snapshot, "to_dict"):
            snapshot_payload = snapshot.to_dict()
        elif isinstance(snapshot, dict):
            snapshot_payload = snapshot
        else:
            snapshot_payload = {}
        quality_summary = snapshot_payload.get("quality_summary", {})
        total_views = snapshot_payload.get("view_counts", {})

        return {
            **snapshot_payload,
            "total_views_compiled": sum(total_views.values()) if isinstance(total_views, dict) else 0,
            "avg_view_quality": float(quality_summary.get("avg_quality", 0.0)),
        }

    def _build_cognition_stability(
        self, snapshot: RuntimeDiagnosticsSnapshot
    ) -> Dict[str, Any]:
        runtime = snapshot.runtime_overview
        if "total_executions" not in runtime:
            return {
                "stability_score": 0.0,
                "stability_classification": "unknown",
                "failure_pressure": 0.0,
            }

        success_rate = float(runtime.get("success_rate", 0.0))
        quality = float(runtime.get("avg_quality_score", 0.0))
        semantic = float(runtime.get("avg_semantic_retention", 0.0))
        token_eff = float(runtime.get("avg_token_efficiency", 0.0))
        failures = float(snapshot.failure_propagation.get("total_failures", 0))
        executions = max(float(runtime.get("total_executions", 1)), 1.0)

        failure_pressure = failures / executions
        stability_score = max(
            0.0,
            min(
                100.0,
                (
                    success_rate * 35.0
                    + quality * 25.0
                    + semantic * 20.0
                    + token_eff * 20.0
                    - failure_pressure * 30.0
                ),
            ),
        )

        if stability_score >= 85:
            classification = "stable"
        elif stability_score >= 70:
            classification = "monitor"
        elif stability_score >= 50:
            classification = "degrading"
        else:
            classification = "critical"

        return {
            "stability_score": stability_score,
            "stability_classification": classification,
            "failure_pressure": failure_pressure,
            "success_rate": success_rate,
            "avg_quality_score": quality,
            "avg_semantic_retention": semantic,
            "avg_token_efficiency": token_eff,
        }
