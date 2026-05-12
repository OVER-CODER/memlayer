"""
Historical Benchmark Persistence and Regression Analysis

Enables longitudinal analysis of compilation performance, semantic drift,
and provider behavior across time. Supports regression detection,
trend analysis, and historical comparisons.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import statistics


@dataclass
class BenchmarkSnapshot:
    """Snapshot of benchmark state at a point in time."""

    timestamp: datetime
    benchmark_id: str

    # Token metrics
    total_raw_tokens: int
    total_compiled_tokens: int
    compression_ratio: float
    tokens_saved: int

    # Latency metrics
    total_latency_ms: float
    avg_stage_latency_ms: float
    bottleneck_stage: str

    # Quality metrics
    quality_score: float
    semantic_drift: float
    degradation_count: int

    # Provider metrics
    best_provider: str
    provider_scores: Dict[str, float]

    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "benchmark_id": self.benchmark_id,
            "token_metrics": {
                "total_raw_tokens": self.total_raw_tokens,
                "total_compiled_tokens": self.total_compiled_tokens,
                "compression_ratio": self.compression_ratio,
                "tokens_saved": self.tokens_saved,
            },
            "latency_metrics": {
                "total_latency_ms": self.total_latency_ms,
                "avg_stage_latency_ms": self.avg_stage_latency_ms,
                "bottleneck_stage": self.bottleneck_stage,
            },
            "quality_metrics": {
                "quality_score": self.quality_score,
                "semantic_drift": self.semantic_drift,
                "degradation_count": self.degradation_count,
            },
            "provider_metrics": {
                "best_provider": self.best_provider,
                "provider_scores": self.provider_scores,
            },
        }


@dataclass
class RegressionEvent:
    """Detected regression in performance."""

    timestamp: datetime
    metric: str  # What regressed (latency, quality, compression, etc)
    previous_value: float
    current_value: float
    change_percentage: float
    severity: str  # minor, medium, critical
    details: Dict


class BenchmarkHistoryStore:
    """Persistent storage for benchmark history."""

    def __init__(self, storage_dir: str = "benchmarks/history"):
        """Initialize benchmark history store."""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.current_snapshots: List[BenchmarkSnapshot] = []
        self._load_existing()

    def _load_existing(self) -> None:
        """Load existing benchmark history from disk."""
        history_file = self.storage_dir / "history.jsonl"

        if history_file.exists():
            with open(history_file, "r") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        # Could reconstruct snapshots here if needed
                    except json.JSONDecodeError:
                        continue

    def record_snapshot(self, snapshot: BenchmarkSnapshot) -> None:
        """Record a benchmark snapshot."""
        self.current_snapshots.append(snapshot)
        self._persist_snapshot(snapshot)

    def _persist_snapshot(self, snapshot: BenchmarkSnapshot) -> None:
        """Persist snapshot to disk."""
        history_file = self.storage_dir / "history.jsonl"

        with open(history_file, "a") as f:
            f.write(json.dumps(snapshot.to_dict(), default=str) + "\n")

    def get_recent_snapshots(self, days: int = 7) -> List[BenchmarkSnapshot]:
        """Get snapshots from the last N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [s for s in self.current_snapshots if s.timestamp >= cutoff]

    def get_snapshots_by_benchmark(self, benchmark_id: str) -> List[BenchmarkSnapshot]:
        """Get all snapshots for a specific benchmark."""
        return [s for s in self.current_snapshots if s.benchmark_id == benchmark_id]


class RegressionAnalyzer:
    """Analyzes performance regressions."""

    def __init__(self, store: BenchmarkHistoryStore):
        """Initialize regression analyzer."""
        self.store = store
        self.regressions: List[RegressionEvent] = []

    def detect_regressions(self, threshold_pct: float = 10.0) -> List[RegressionEvent]:
        """Detect performance regressions."""
        regressions = []

        recent = self.store.get_recent_snapshots(days=7)
        if len(recent) < 2:
            return regressions

        # Sort by timestamp
        recent = sorted(recent, key=lambda x: x.timestamp)

        # Compare consecutive snapshots
        for i in range(1, len(recent)):
            prev = recent[i - 1]
            curr = recent[i]

            # Check latency regression
            latency_change = (
                (
                    (curr.total_latency_ms - prev.total_latency_ms)
                    / prev.total_latency_ms
                    * 100
                )
                if prev.total_latency_ms > 0
                else 0
            )

            if latency_change > threshold_pct:
                regressions.append(
                    RegressionEvent(
                        timestamp=curr.timestamp,
                        metric="latency_ms",
                        previous_value=prev.total_latency_ms,
                        current_value=curr.total_latency_ms,
                        change_percentage=latency_change,
                        severity=self._severity(latency_change),
                        details={"stage": "total"},
                    )
                )

            # Check quality regression
            quality_change = (
                ((prev.quality_score - curr.quality_score) / prev.quality_score * 100)
                if prev.quality_score > 0
                else 0
            )

            if quality_change > threshold_pct:
                regressions.append(
                    RegressionEvent(
                        timestamp=curr.timestamp,
                        metric="quality_score",
                        previous_value=prev.quality_score,
                        current_value=curr.quality_score,
                        change_percentage=quality_change,
                        severity=self._severity(quality_change),
                        details={"drift": curr.semantic_drift},
                    )
                )

            # Check compression ratio degradation
            ratio_change = (
                (
                    (curr.compression_ratio - prev.compression_ratio)
                    / prev.compression_ratio
                    * 100
                )
                if prev.compression_ratio > 0
                else 0
            )

            if ratio_change > threshold_pct:  # Ratio increased (worse compression)
                regressions.append(
                    RegressionEvent(
                        timestamp=curr.timestamp,
                        metric="compression_ratio",
                        previous_value=prev.compression_ratio,
                        current_value=curr.compression_ratio,
                        change_percentage=ratio_change,
                        severity=self._severity(ratio_change),
                        details={"tokens_saved": curr.tokens_saved},
                    )
                )

        self.regressions.extend(regressions)
        return regressions

    def _severity(self, change_pct: float) -> str:
        """Determine severity based on change percentage."""
        if change_pct > 50:
            return "critical"
        elif change_pct > 25:
            return "medium"
        else:
            return "minor"

    def get_regressions(self) -> List[Dict]:
        """Export all detected regressions."""
        return [
            {
                "timestamp": r.timestamp.isoformat(),
                "metric": r.metric,
                "previous_value": r.previous_value,
                "current_value": r.current_value,
                "change_percentage": r.change_percentage,
                "severity": r.severity,
            }
            for r in self.regressions
        ]


class TrendAnalyzer:
    """Analyzes performance trends over time."""

    def __init__(self, store: BenchmarkHistoryStore):
        """Initialize trend analyzer."""
        self.store = store

    def analyze_trend(self, benchmark_id: str, metric: str, days: int = 30) -> Dict:
        """Analyze trend for a specific metric."""
        snapshots = self.store.get_snapshots_by_benchmark(benchmark_id)

        if not snapshots:
            return {}

        # Filter by date range
        cutoff = datetime.utcnow() - timedelta(days=days)
        snapshots = [s for s in snapshots if s.timestamp >= cutoff]
        snapshots = sorted(snapshots, key=lambda x: x.timestamp)

        if not snapshots:
            return {}

        # Extract metric values
        values = self._extract_metric_values(snapshots, metric)

        if not values:
            return {}

        # Compute statistics
        return {
            "metric": metric,
            "benchmark_id": benchmark_id,
            "days": days,
            "num_samples": len(values),
            "min": min(values),
            "max": max(values),
            "avg": statistics.mean(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0,
            "trend": self._compute_trend(values),
            "first_value": values[0],
            "last_value": values[-1],
            "total_change": values[-1] - values[0],
            "change_percentage": ((values[-1] - values[0]) / values[0] * 100)
            if values[0] != 0
            else 0,
        }

    def _extract_metric_values(
        self, snapshots: List[BenchmarkSnapshot], metric: str
    ) -> List[float]:
        """Extract metric values from snapshots."""
        values = []

        for snapshot in snapshots:
            if metric == "latency_ms":
                values.append(snapshot.total_latency_ms)
            elif metric == "quality_score":
                values.append(snapshot.quality_score)
            elif metric == "compression_ratio":
                values.append(snapshot.compression_ratio)
            elif metric == "tokens_saved":
                values.append(snapshot.tokens_saved)
            elif metric == "semantic_drift":
                values.append(snapshot.semantic_drift)

        return values

    def _compute_trend(self, values: List[float]) -> str:
        """Compute trend direction."""
        if len(values) < 2:
            return "insufficient_data"

        # Simple linear trend
        first_half_avg = statistics.mean(values[: len(values) // 2])
        second_half_avg = statistics.mean(values[len(values) // 2 :])

        if second_half_avg > first_half_avg * 1.05:
            return "degrading"
        elif second_half_avg < first_half_avg * 0.95:
            return "improving"
        else:
            return "stable"


class ComparisonAnalyzer:
    """Analyzes comparisons across time and providers."""

    def __init__(self, store: BenchmarkHistoryStore):
        """Initialize comparison analyzer."""
        self.store = store

    def compare_snapshots(self, snapshot_ids: List[str]) -> Dict:
        """Compare multiple snapshots."""
        snapshots = [
            s for s in self.store.current_snapshots if s.benchmark_id in snapshot_ids
        ]

        if not snapshots:
            return {}

        return {
            "num_snapshots": len(snapshots),
            "date_range": {
                "earliest": min(s.timestamp for s in snapshots).isoformat(),
                "latest": max(s.timestamp for s in snapshots).isoformat(),
            },
            "latency_stats": self._compare_latency(snapshots),
            "quality_stats": self._compare_quality(snapshots),
            "compression_stats": self._compare_compression(snapshots),
            "provider_stats": self._compare_providers(snapshots),
        }

    def _compare_latency(self, snapshots: List[BenchmarkSnapshot]) -> Dict:
        """Compare latency across snapshots."""
        latencies = [s.total_latency_ms for s in snapshots]
        return {
            "min": min(latencies),
            "max": max(latencies),
            "avg": statistics.mean(latencies),
            "median": statistics.median(latencies),
            "variance": statistics.variance(latencies) if len(latencies) > 1 else 0,
        }

    def _compare_quality(self, snapshots: List[BenchmarkSnapshot]) -> Dict:
        """Compare quality across snapshots."""
        qualities = [s.quality_score for s in snapshots]
        drifts = [s.semantic_drift for s in snapshots]

        return {
            "avg_quality": statistics.mean(qualities),
            "min_quality": min(qualities),
            "max_quality": max(qualities),
            "avg_drift": statistics.mean(drifts),
            "max_drift": max(drifts),
        }

    def _compare_compression(self, snapshots: List[BenchmarkSnapshot]) -> Dict:
        """Compare compression across snapshots."""
        ratios = [s.compression_ratio for s in snapshots]
        savings = [s.tokens_saved for s in snapshots]

        return {
            "avg_ratio": statistics.mean(ratios),
            "best_ratio": min(ratios),
            "worst_ratio": max(ratios),
            "total_tokens_saved": sum(savings),
            "avg_tokens_saved": statistics.mean(savings),
        }

    def _compare_providers(self, snapshots: List[BenchmarkSnapshot]) -> Dict:
        """Compare provider performance."""
        all_providers = set()
        for s in snapshots:
            all_providers.update(s.provider_scores.keys())

        provider_stats = {}
        for provider in all_providers:
            scores = [s.provider_scores.get(provider, 0) for s in snapshots]
            provider_stats[provider] = {
                "avg_score": statistics.mean(scores) if scores else 0,
                "min_score": min(scores) if scores else 0,
                "max_score": max(scores) if scores else 0,
                "wins": sum(1 for s in snapshots if s.best_provider == provider),
            }

        return provider_stats


class BenchmarkReportGenerator:
    """Generates comprehensive benchmark reports."""

    def __init__(self, store: BenchmarkHistoryStore):
        """Initialize report generator."""
        self.store = store
        self.regression_analyzer = RegressionAnalyzer(store)
        self.trend_analyzer = TrendAnalyzer(store)
        self.comparison_analyzer = ComparisonAnalyzer(store)

    def generate_performance_report(self, days: int = 30) -> Dict:
        """Generate comprehensive performance report."""
        recent = self.store.get_recent_snapshots(days=days)

        if not recent:
            return {"status": "insufficient_data"}

        regressions = self.regression_analyzer.detect_regressions()

        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "period_days": days,
            "num_benchmarks": len(recent),
            "date_range": {
                "start": min(s.timestamp for s in recent).isoformat(),
                "end": max(s.timestamp for s in recent).isoformat(),
            },
            "summary": {
                "avg_latency_ms": statistics.mean([s.total_latency_ms for s in recent]),
                "avg_quality": statistics.mean([s.quality_score for s in recent]),
                "avg_compression_ratio": statistics.mean(
                    [s.compression_ratio for s in recent]
                ),
                "total_tokens_saved": sum(s.tokens_saved for s in recent),
            },
            "regressions": self.regression_analyzer.get_regressions(),
            "regression_count": len(regressions),
            "critical_regressions": len(
                [r for r in regressions if r.severity == "critical"]
            ),
            "providers": self._provider_summary(recent),
        }

        return report

    def _provider_summary(self, snapshots: List[BenchmarkSnapshot]) -> Dict:
        """Summarize provider performance."""
        provider_wins = {}

        for snapshot in snapshots:
            best = snapshot.best_provider
            if best not in provider_wins:
                provider_wins[best] = 0
            provider_wins[best] += 1

        return {
            "best_providers": provider_wins,
            "total_comparisons": len(snapshots),
        }

    def generate_regression_report(self) -> Dict:
        """Generate regression analysis report."""
        regressions = self.regression_analyzer.detect_regressions()

        if not regressions:
            return {
                "status": "no_regressions_detected",
                "total_regressions": 0,
                "by_metric": {},
                "by_severity": {},
            }

        by_metric = {}
        for r in regressions:
            if r.metric not in by_metric:
                by_metric[r.metric] = []
            by_metric[r.metric].append(asdict(r))

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "total_regressions": len(regressions),
            "by_metric": by_metric,
            "by_severity": self._group_by_severity(regressions),
        }

    def _group_by_severity(self, regressions: List[RegressionEvent]) -> Dict:
        """Group regressions by severity."""
        grouped = {"critical": [], "medium": [], "minor": []}

        for r in regressions:
            grouped[r.severity].append(
                {
                    "metric": r.metric,
                    "change_percentage": r.change_percentage,
                    "timestamp": r.timestamp.isoformat(),
                }
            )

        return grouped
