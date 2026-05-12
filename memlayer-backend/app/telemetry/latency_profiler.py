"""
Latency Profiler for Phase 5.

Provides per-stage latency measurement, bottleneck analysis,
percentile distributions, and latency trend tracking.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from enum import Enum
import statistics
import logging
import json

logger = logging.getLogger(__name__)


class LatencyLevel(Enum):
    """Latency classification."""

    EXCELLENT = "excellent"  # < 10ms
    GOOD = "good"  # 10-50ms
    ACCEPTABLE = "acceptable"  # 50-200ms
    SLOW = "slow"  # 200-1000ms
    VERY_SLOW = "very_slow"  # > 1000ms


@dataclass
class PercentileStats:
    """Percentile statistics for latency."""

    p50: float = 0.0  # Median
    p75: float = 0.0
    p90: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    p99_9: float = 0.0  # 99.9th percentile
    min: float = 0.0
    max: float = 0.0
    mean: float = 0.0
    std_dev: float = 0.0
    count: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class StageLatencyMetrics:
    """Latency metrics for a single pipeline stage."""

    stage_name: str
    timestamp: datetime
    duration_ms: float

    # Categorization
    stage_level: LatencyLevel = LatencyLevel.GOOD
    is_bottleneck: bool = False

    # Input/output sizes
    input_size_items: int = 0
    output_size_items: int = 0

    # Metadata
    provider: str = "generic"
    compression_mode: str = "balanced"
    query_type: str = "unknown"
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "stage_name": self.stage_name,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "stage_level": self.stage_level.value,
            "is_bottleneck": self.is_bottleneck,
            "input_size_items": self.input_size_items,
            "output_size_items": self.output_size_items,
            "provider": self.provider,
            "compression_mode": self.compression_mode,
            "query_type": self.query_type,
            "metadata": self.metadata,
        }


@dataclass
class PipelineLatencyProfile:
    """Complete latency profile for a pipeline execution."""

    profile_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_duration_ms: float = 0.0

    # Stages
    stages: List[StageLatencyMetrics] = field(default_factory=list)

    # Bottleneck analysis
    bottleneck_stage: Optional[str] = None
    bottleneck_percentage: float = 0.0

    # Metadata
    provider: str = "generic"
    compression_mode: str = "balanced"
    query_type: str = "unknown"
    input_memories_count: int = 0
    metadata: Dict = field(default_factory=dict)

    def add_stage(self, stage_metric: StageLatencyMetrics) -> None:
        """Add a stage to the profile."""
        self.stages.append(stage_metric)

    def finalize(self) -> None:
        """Finalize profile and identify bottlenecks."""
        if not self.stages:
            return

        # Calculate total duration
        self.total_duration_ms = sum(s.duration_ms for s in self.stages)

        # Find bottleneck stage
        if self.total_duration_ms > 0:
            max_duration = 0.0
            bottleneck_stage = None

            for stage in self.stages:
                if stage.duration_ms > max_duration:
                    max_duration = stage.duration_ms
                    bottleneck_stage = stage.stage_name
                    stage.is_bottleneck = True

            self.bottleneck_stage = bottleneck_stage
            self.bottleneck_percentage = (max_duration / self.total_duration_ms) * 100

            # Mark only the bottleneck stage
            for stage in self.stages:
                if stage.stage_name != bottleneck_stage:
                    stage.is_bottleneck = False

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "profile_id": self.profile_id,
            "timestamp": self.timestamp.isoformat(),
            "total_duration_ms": self.total_duration_ms,
            "stages": [s.to_dict() for s in self.stages],
            "bottleneck_stage": self.bottleneck_stage,
            "bottleneck_percentage": self.bottleneck_percentage,
            "provider": self.provider,
            "compression_mode": self.compression_mode,
            "query_type": self.query_type,
            "input_memories_count": self.input_memories_count,
            "metadata": self.metadata,
        }


class LatencyProfiler:
    """
    Comprehensive latency profiling for the compiler pipeline.

    Tracks per-stage latency, identifies bottlenecks, calculates percentiles,
    and generates latency trends.
    """

    def __init__(self, max_history: int = 10000):
        """
        Initialize latency profiler.

        Args:
            max_history: Maximum profiles to keep in memory
        """
        self.max_history = max_history
        self.profiles: List[PipelineLatencyProfile] = []

        # Stage latency history for percentile calculations
        self.stage_latencies: Dict[str, List[float]] = defaultdict(list)

    def create_profile(
        self,
        profile_id: str,
        provider: str = "generic",
        compression_mode: str = "balanced",
        query_type: str = "unknown",
        input_memories_count: int = 0,
    ) -> PipelineLatencyProfile:
        """Create a new latency profile."""
        profile = PipelineLatencyProfile(
            profile_id=profile_id,
            provider=provider,
            compression_mode=compression_mode,
            query_type=query_type,
            input_memories_count=input_memories_count,
        )
        logger.debug(f"Created latency profile {profile_id}")
        return profile

    def record_stage_latency(
        self,
        profile: PipelineLatencyProfile,
        stage_name: str,
        duration_ms: float,
        input_size_items: int = 0,
        output_size_items: int = 0,
    ) -> None:
        """Record latency for a pipeline stage."""
        # Determine stage level
        if duration_ms < 10:
            stage_level = LatencyLevel.EXCELLENT
        elif duration_ms < 50:
            stage_level = LatencyLevel.GOOD
        elif duration_ms < 200:
            stage_level = LatencyLevel.ACCEPTABLE
        elif duration_ms < 1000:
            stage_level = LatencyLevel.SLOW
        else:
            stage_level = LatencyLevel.VERY_SLOW

        metric = StageLatencyMetrics(
            stage_name=stage_name,
            timestamp=datetime.now(timezone.utc),
            duration_ms=duration_ms,
            stage_level=stage_level,
            input_size_items=input_size_items,
            output_size_items=output_size_items,
            provider=profile.provider,
            compression_mode=profile.compression_mode,
            query_type=profile.query_type,
        )

        profile.add_stage(metric)

        # Track in history
        self.stage_latencies[stage_name].append(duration_ms)

        # Trim stage history if needed
        if len(self.stage_latencies[stage_name]) > self.max_history:
            self.stage_latencies[stage_name] = self.stage_latencies[stage_name][
                -self.max_history :
            ]

        logger.debug(
            f"Recorded stage {stage_name} latency: {duration_ms:.2f}ms "
            f"({stage_level.value})"
        )

    def finalize_profile(self, profile: PipelineLatencyProfile) -> None:
        """Finalize a latency profile."""
        profile.finalize()
        self.profiles.append(profile)

        # Trim history
        if len(self.profiles) > self.max_history:
            self.profiles = self.profiles[-self.max_history :]

        logger.debug(
            f"Finalized profile {profile.profile_id}: "
            f"total={profile.total_duration_ms:.2f}ms, "
            f"bottleneck={profile.bottleneck_stage} "
            f"({profile.bottleneck_percentage:.1f}%)"
        )

    def get_stage_percentiles(
        self, stage_name: str, lookback_profiles: Optional[int] = None
    ) -> PercentileStats:
        """Get percentile statistics for a stage."""
        latencies = self.stage_latencies.get(stage_name, [])

        if lookback_profiles:
            # Get latencies from recent profiles only
            recent_latencies = []
            for profile in self.profiles[-lookback_profiles:]:
                for stage in profile.stages:
                    if stage.stage_name == stage_name:
                        recent_latencies.append(stage.duration_ms)
            latencies = recent_latencies

        if not latencies:
            return PercentileStats()

        sorted_latencies = sorted(latencies)
        count = len(sorted_latencies)

        def percentile(p: float) -> float:
            index = (p / 100.0) * (count - 1)
            lower = int(index)
            upper = lower + 1
            weight = index - lower

            if upper >= count:
                return sorted_latencies[-1]

            return (
                sorted_latencies[lower] * (1 - weight)
                + sorted_latencies[upper] * weight
            )

        mean_val = sum(latencies) / count if latencies else 0.0
        variance = (
            sum((x - mean_val) ** 2 for x in latencies) / count if latencies else 0.0
        )
        std_dev = variance**0.5

        return PercentileStats(
            p50=percentile(50),
            p75=percentile(75),
            p90=percentile(90),
            p95=percentile(95),
            p99=percentile(99),
            p99_9=percentile(99.9),
            min=min(latencies),
            max=max(latencies),
            mean=mean_val,
            std_dev=std_dev,
            count=count,
        )

    def get_bottleneck_analysis(self, lookback_profiles: Optional[int] = None) -> Dict:
        """Analyze bottleneck stages across profiles."""
        profiles = (
            self.profiles[-lookback_profiles:] if lookback_profiles else self.profiles
        )

        if not profiles:
            return {"message": "No profiles recorded"}

        bottleneck_counts = defaultdict(int)
        total_bottleneck_time = defaultdict(float)

        for profile in profiles:
            if profile.bottleneck_stage:
                bottleneck_counts[profile.bottleneck_stage] += 1
                # Find the bottleneck stage metrics
                for stage in profile.stages:
                    if stage.stage_name == profile.bottleneck_stage:
                        total_bottleneck_time[profile.bottleneck_stage] += (
                            stage.duration_ms
                        )

        # Sort by frequency
        sorted_bottlenecks = sorted(
            bottleneck_counts.items(), key=lambda x: x[1], reverse=True
        )

        analysis = {
            "total_profiles_analyzed": len(profiles),
            "bottlenecks": [
                {
                    "stage": stage_name,
                    "frequency": count,
                    "frequency_percentage": (count / len(profiles)) * 100,
                    "total_bottleneck_time_ms": total_bottleneck_time[stage_name],
                    "avg_bottleneck_time_ms": (
                        total_bottleneck_time[stage_name] / count if count > 0 else 0
                    ),
                }
                for stage_name, count in sorted_bottlenecks
            ],
        }

        return analysis

    def get_latency_heatmap(
        self,
        stage_name: Optional[str] = None,
        hours: int = 24,
        bucket_size_minutes: int = 60,
    ) -> List[Dict]:
        """Get latency trend data for visualization."""
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(hours=hours)

        # Collect relevant metrics
        metrics = []
        for profile in self.profiles:
            if profile.timestamp < cutoff_time:
                continue

            for stage in profile.stages:
                if stage_name and stage.stage_name != stage_name:
                    continue
                metrics.append(
                    {
                        "timestamp": stage.timestamp,
                        "stage": stage.stage_name,
                        "duration_ms": stage.duration_ms,
                        "level": stage.stage_level.value,
                    }
                )

        if not metrics:
            return []

        # Bucket by time
        buckets = defaultdict(list)
        for metric in metrics:
            bucket_time = metric["timestamp"].replace(minute=0, second=0, microsecond=0)
            bucket_key = bucket_time.isoformat()

            if stage_name:
                buckets[bucket_key].append(metric["duration_ms"])
            else:
                # Group by stage
                stage_key = f"{bucket_key}|{metric['stage']}"
                buckets[stage_key].append(metric["duration_ms"])

        # Generate heatmap data
        heatmap = []
        for bucket_key in sorted(buckets.keys()):
            values = buckets[bucket_key]
            avg = sum(values) / len(values) if values else 0.0
            max_val = max(values) if values else 0.0
            min_val = min(values) if values else 0.0

            if "|" in bucket_key:
                timestamp, stage = bucket_key.rsplit("|", 1)
            else:
                timestamp = bucket_key
                stage = stage_name or "all"

            heatmap.append(
                {
                    "timestamp": timestamp,
                    "stage": stage,
                    "avg_latency_ms": avg,
                    "max_latency_ms": max_val,
                    "min_latency_ms": min_val,
                    "sample_count": len(values),
                }
            )

        return heatmap

    def get_stage_comparison(self) -> Dict[str, Dict]:
        """Compare latency characteristics across all stages."""
        comparison = {}

        for stage_name in self.stage_latencies:
            percentiles = self.get_stage_percentiles(stage_name)
            comparison[stage_name] = {
                "percentiles": percentiles.to_dict(),
                "classification": self._classify_stage_latency(percentiles.mean),
            }

        return comparison

    def _classify_stage_latency(self, mean_latency_ms: float) -> str:
        """Classify stage based on mean latency."""
        if mean_latency_ms < 10:
            return "excellent"
        elif mean_latency_ms < 50:
            return "good"
        elif mean_latency_ms < 200:
            return "acceptable"
        elif mean_latency_ms < 1000:
            return "slow"
        else:
            return "very_slow"

    def get_provider_comparison(self) -> Dict[str, Dict]:
        """Compare latency across providers."""
        provider_stats = defaultdict(list)

        for profile in self.profiles:
            provider_stats[profile.provider].append(profile.total_duration_ms)

        comparison = {}
        for provider, latencies in provider_stats.items():
            if latencies:
                comparison[provider] = {
                    "runs": len(latencies),
                    "avg_latency_ms": sum(latencies) / len(latencies),
                    "min_latency_ms": min(latencies),
                    "max_latency_ms": max(latencies),
                    "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)],
                }

        return comparison

    def get_compression_mode_comparison(self) -> Dict[str, Dict]:
        """Compare latency across compression modes."""
        mode_stats = defaultdict(list)

        for profile in self.profiles:
            mode_stats[profile.compression_mode].append(profile.total_duration_ms)

        comparison = {}
        for mode, latencies in mode_stats.items():
            if latencies:
                comparison[mode] = {
                    "runs": len(latencies),
                    "avg_latency_ms": sum(latencies) / len(latencies),
                    "min_latency_ms": min(latencies),
                    "max_latency_ms": max(latencies),
                    "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)],
                }

        return comparison

    def get_profiler_report(self) -> Dict:
        """Generate comprehensive profiler report."""
        if not self.profiles:
            return {"message": "No latency profiles recorded"}

        total_duration = sum(p.total_duration_ms for p in self.profiles)
        avg_duration = total_duration / len(self.profiles) if self.profiles else 0.0

        return {
            "total_profiles": len(self.profiles),
            "total_pipeline_duration_ms": total_duration,
            "avg_pipeline_duration_ms": avg_duration,
            "stage_comparison": self.get_stage_comparison(),
            "provider_comparison": self.get_provider_comparison(),
            "compression_mode_comparison": self.get_compression_mode_comparison(),
            "bottleneck_analysis": self.get_bottleneck_analysis(lookback_profiles=1000),
        }

    def export_profiles(self, output_file: str) -> str:
        """Export latency profiles to JSON file."""
        report = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_profiles": len(self.profiles),
            "profiles": [p.to_dict() for p in self.profiles[-1000:]],  # Last 1000
            "report": self.get_profiler_report(),
        }

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Exported latency profiles to {output_file}")
        return output_file


# Global latency profiler instance
_latency_profiler: Optional[LatencyProfiler] = None


def get_latency_profiler() -> LatencyProfiler:
    """Get or create the global latency profiler."""
    global _latency_profiler
    if _latency_profiler is None:
        _latency_profiler = LatencyProfiler()
    return _latency_profiler
