"""
Semantic Drift Analyzer for Phase 5.

Tracks longitudinal semantic degradation across compression cycles,
entity erosion, reasoning continuity, and semantic quality regression.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
import statistics
import logging
import json

logger = logging.getLogger(__name__)


class DriftLevel(Enum):
    """Semantic drift classification."""

    STABLE = "stable"  # < 5% degradation
    MINOR = "minor"  # 5-15% degradation
    MODERATE = "moderate"  # 15-30% degradation
    SIGNIFICANT = "significant"  # 30-50% degradation
    CRITICAL = "critical"  # > 50% degradation


@dataclass
class EntityDriftMetrics:
    """Tracking entity erosion across compression cycles."""

    cycle_number: int
    entities_input: int = 0
    entities_preserved: int = 0
    entities_lost: int = 0
    entity_preservation_ratio: float = 0.0  # preserved / input

    # Entity types tracking
    key_entities_preserved: List[str] = field(default_factory=list)
    key_entities_lost: List[str] = field(default_factory=list)

    def calculate_preservation_ratio(self) -> float:
        """Calculate entity preservation ratio."""
        if self.entities_input == 0:
            return 0.0
        self.entity_preservation_ratio = self.entities_preserved / self.entities_input
        return self.entity_preservation_ratio

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "cycle_number": self.cycle_number,
            "entities_input": self.entities_input,
            "entities_preserved": self.entities_preserved,
            "entities_lost": self.entities_lost,
            "entity_preservation_ratio": self.entity_preservation_ratio,
            "key_entities_preserved": self.key_entities_preserved,
            "key_entities_lost": self.key_entities_lost,
        }


@dataclass
class ReasoningContinuityMetrics:
    """Tracking reasoning chain continuity across cycles."""

    cycle_number: int
    reasoning_chains_input: int = 0
    reasoning_chains_preserved: int = 0
    reasoning_chains_broken: int = 0
    continuity_score: float = 0.0  # 0-1, how well reasoning is preserved

    # Types of reasoning chains tracked
    logical_chains: int = 0
    causal_chains: int = 0
    temporal_chains: int = 0

    # Preservation of each type
    logical_chains_preserved: int = 0
    causal_chains_preserved: int = 0
    temporal_chains_preserved: int = 0

    def calculate_continuity(self) -> float:
        """Calculate overall continuity score."""
        if self.reasoning_chains_input == 0:
            return 0.0
        self.continuity_score = (
            self.reasoning_chains_preserved / self.reasoning_chains_input
        )
        return self.continuity_score

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "cycle_number": self.cycle_number,
            "reasoning_chains_input": self.reasoning_chains_input,
            "reasoning_chains_preserved": self.reasoning_chains_preserved,
            "reasoning_chains_broken": self.reasoning_chains_broken,
            "continuity_score": self.continuity_score,
            "logical_chains_preserved": self.logical_chains_preserved,
            "causal_chains_preserved": self.causal_chains_preserved,
            "temporal_chains_preserved": self.temporal_chains_preserved,
        }


@dataclass
class CompressionCycleDrift:
    """Semantic metrics for a single compression cycle."""

    cycle_number: int
    timestamp: datetime
    compression_ratio: float = 0.0

    # Semantic quality metrics
    semantic_density_before: float = 0.0
    semantic_density_after: float = 0.0
    semantic_density_degradation: float = 0.0

    # Content preservation
    entity_metrics: EntityDriftMetrics = field(
        default_factory=lambda: EntityDriftMetrics(0)
    )
    reasoning_metrics: ReasoningContinuityMetrics = field(
        default_factory=lambda: ReasoningContinuityMetrics(0)
    )

    # Topic/context preservation
    topic_preservation: float = 0.0  # 0-1
    reasoning_preservation: float = 0.0  # 0-1
    detail_preservation: float = 0.0  # 0-1

    # Overall drift
    overall_drift_level: DriftLevel = DriftLevel.STABLE
    drift_percentage: float = 0.0  # 0-100

    # Metadata
    provider: str = "generic"
    compression_mode: str = "balanced"
    query_type: str = "unknown"
    metadata: Dict = field(default_factory=dict)

    def calculate_degradation(self) -> None:
        """Calculate semantic degradation metrics."""
        self.semantic_density_degradation = max(
            0.0,
            self.semantic_density_before - self.semantic_density_after,
        )

        # Calculate overall drift percentage
        if self.semantic_density_before > 0:
            drift_pct = (
                self.semantic_density_degradation / self.semantic_density_before
            ) * 100
        else:
            drift_pct = 0.0

        self.drift_percentage = drift_pct

        # Classify drift level
        if drift_pct < 5:
            self.overall_drift_level = DriftLevel.STABLE
        elif drift_pct < 15:
            self.overall_drift_level = DriftLevel.MINOR
        elif drift_pct < 30:
            self.overall_drift_level = DriftLevel.MODERATE
        elif drift_pct < 50:
            self.overall_drift_level = DriftLevel.SIGNIFICANT
        else:
            self.overall_drift_level = DriftLevel.CRITICAL

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "cycle_number": self.cycle_number,
            "timestamp": self.timestamp.isoformat(),
            "compression_ratio": self.compression_ratio,
            "semantic_density_before": self.semantic_density_before,
            "semantic_density_after": self.semantic_density_after,
            "semantic_density_degradation": self.semantic_density_degradation,
            "entity_metrics": self.entity_metrics.to_dict(),
            "reasoning_metrics": self.reasoning_metrics.to_dict(),
            "topic_preservation": self.topic_preservation,
            "reasoning_preservation": self.reasoning_preservation,
            "detail_preservation": self.detail_preservation,
            "overall_drift_level": self.overall_drift_level.value,
            "drift_percentage": self.drift_percentage,
            "provider": self.provider,
            "compression_mode": self.compression_mode,
            "query_type": self.query_type,
            "metadata": self.metadata,
        }


@dataclass
class SemanticDriftSession:
    """Session tracking semantic drift across multiple compression cycles."""

    session_id: str
    query: str
    query_type: str = "unknown"
    provider: str = "generic"
    compression_mode: str = "balanced"

    # Timeline
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Cycles
    cycles: List[CompressionCycleDrift] = field(default_factory=list)

    # Summary
    max_drift_level: DriftLevel = DriftLevel.STABLE
    total_degradation: float = 0.0
    cumulative_entity_loss: float = 0.0
    cumulative_reasoning_loss: float = 0.0

    def add_cycle(self, cycle: CompressionCycleDrift) -> None:
        """Add a compression cycle."""
        self.cycles.append(cycle)

    def finalize(self) -> None:
        """Finalize session analysis."""
        self.completed_at = datetime.utcnow()

        if not self.cycles:
            return

        # Find max drift level
        max_level_value = 0
        max_level = DriftLevel.STABLE
        for level in DriftLevel:
            if any(c.overall_drift_level == level for c in self.cycles):
                if level.value in [
                    "critical",
                    "significant",
                    "moderate",
                    "minor",
                    "stable",
                ]:
                    level_map = {
                        "stable": 1,
                        "minor": 2,
                        "moderate": 3,
                        "significant": 4,
                        "critical": 5,
                    }
                    if level_map[level.value] > max_level_value:
                        max_level_value = level_map[level.value]
                        max_level = level

        self.max_drift_level = max_level

        # Calculate cumulative losses
        for cycle in self.cycles:
            self.total_degradation += cycle.drift_percentage
            if cycle.entity_metrics:
                self.cumulative_entity_loss += max(
                    0, cycle.entity_metrics.entities_lost
                )
            if cycle.reasoning_metrics:
                self.cumulative_reasoning_loss += max(
                    0, cycle.reasoning_metrics.reasoning_chains_broken
                )

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "query": self.query,
            "query_type": self.query_type,
            "provider": self.provider,
            "compression_mode": self.compression_mode,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "total_cycles": len(self.cycles),
            "cycles": [c.to_dict() for c in self.cycles],
            "max_drift_level": self.max_drift_level.value,
            "total_degradation": self.total_degradation,
            "cumulative_entity_loss": self.cumulative_entity_loss,
            "cumulative_reasoning_loss": self.cumulative_reasoning_loss,
        }


class SemanticDriftAnalyzer:
    """
    Longitudinal semantic degradation tracking.

    Monitors entity erosion, reasoning continuity, and semantic quality
    across compression cycles and sessions.
    """

    def __init__(self, max_sessions: int = 1000):
        """
        Initialize drift analyzer.

        Args:
            max_sessions: Maximum sessions to keep in memory
        """
        self.max_sessions = max_sessions
        self.sessions: List[SemanticDriftSession] = []
        self.current_session: Optional[SemanticDriftSession] = None

    def create_session(
        self,
        session_id: str,
        query: str,
        query_type: str = "unknown",
        provider: str = "generic",
        compression_mode: str = "balanced",
    ) -> SemanticDriftSession:
        """Create a new drift analysis session."""
        session = SemanticDriftSession(
            session_id=session_id,
            query=query,
            query_type=query_type,
            provider=provider,
            compression_mode=compression_mode,
        )
        self.current_session = session
        logger.debug(f"Created drift session {session_id}")
        return session

    def record_cycle(
        self,
        cycle_number: int,
        compression_ratio: float,
        semantic_density_before: float,
        semantic_density_after: float,
        entity_metrics: Optional[EntityDriftMetrics] = None,
        reasoning_metrics: Optional[ReasoningContinuityMetrics] = None,
        topic_preservation: float = 0.0,
        reasoning_preservation: float = 0.0,
        detail_preservation: float = 0.0,
    ) -> CompressionCycleDrift:
        """Record a compression cycle in the current session."""
        if self.current_session is None:
            logger.warning("No active session, creating default session")
            self.create_session("default", "unknown")

        # Create drift metrics for this cycle
        entity_metrics = entity_metrics or EntityDriftMetrics(cycle_number)
        reasoning_metrics = reasoning_metrics or ReasoningContinuityMetrics(
            cycle_number
        )

        cycle = CompressionCycleDrift(
            cycle_number=cycle_number,
            timestamp=datetime.utcnow(),
            compression_ratio=compression_ratio,
            semantic_density_before=semantic_density_before,
            semantic_density_after=semantic_density_after,
            entity_metrics=entity_metrics,
            reasoning_metrics=reasoning_metrics,
            topic_preservation=topic_preservation,
            reasoning_preservation=reasoning_preservation,
            detail_preservation=detail_preservation,
            provider=self.current_session.provider,
            compression_mode=self.current_session.compression_mode,
            query_type=self.current_session.query_type,
        )

        # Calculate degradation
        cycle.calculate_degradation()

        # Add to session
        self.current_session.add_cycle(cycle)

        logger.debug(
            f"Recorded cycle {cycle_number}: {cycle.drift_percentage:.1f}% drift "
            f"({cycle.overall_drift_level.value})"
        )

        return cycle

    def finalize_session(self) -> SemanticDriftSession:
        """Finalize the current session."""
        if self.current_session is None:
            logger.warning("No active session to finalize")
            return SemanticDriftSession(session_id="empty", query="")

        self.current_session.finalize()
        self.sessions.append(self.current_session)

        # Trim history
        if len(self.sessions) > self.max_sessions:
            self.sessions = self.sessions[-self.max_sessions :]

        session_id = self.current_session.session_id
        logger.debug(
            f"Finalized session {session_id}: "
            f"max_drift={self.current_session.max_drift_level.value}, "
            f"total_degradation={self.current_session.total_degradation:.1f}%"
        )

        result = self.current_session
        self.current_session = None
        return result

    def get_session(self, session_id: str) -> Optional[SemanticDriftSession]:
        """Get a specific session by ID."""
        for session in self.sessions:
            if session.session_id == session_id:
                return session
        return None

    def get_recent_sessions(self, limit: int = 100) -> List[SemanticDriftSession]:
        """Get recent sessions."""
        return self.sessions[-limit:]

    def get_drift_statistics(self, lookback_sessions: Optional[int] = None) -> Dict:
        """Get drift statistics across sessions."""
        sessions = (
            self.sessions[-lookback_sessions:] if lookback_sessions else self.sessions
        )

        if not sessions:
            return {"message": "No sessions recorded"}

        total_sessions = len(sessions)
        total_cycles = sum(len(s.cycles) for s in sessions)

        # Drift level distribution
        drift_distribution = defaultdict(int)
        for session in sessions:
            drift_distribution[session.max_drift_level.value] += 1

        # Average degradation
        total_degradation = sum(s.total_degradation for s in sessions)
        avg_degradation = (
            total_degradation / total_sessions if total_sessions > 0 else 0
        )

        # Entity loss tracking
        total_entity_loss = sum(s.cumulative_entity_loss for s in sessions)
        avg_entity_loss = (
            total_entity_loss / total_sessions if total_sessions > 0 else 0
        )

        # Reasoning loss tracking
        total_reasoning_loss = sum(s.cumulative_reasoning_loss for s in sessions)
        avg_reasoning_loss = (
            total_reasoning_loss / total_sessions if total_sessions > 0 else 0
        )

        return {
            "total_sessions": total_sessions,
            "total_cycles": total_cycles,
            "avg_cycles_per_session": total_cycles / total_sessions
            if total_sessions > 0
            else 0,
            "drift_distribution": dict(drift_distribution),
            "avg_degradation_percentage": avg_degradation,
            "total_entity_loss": total_entity_loss,
            "avg_entity_loss_per_session": avg_entity_loss,
            "total_reasoning_loss": total_reasoning_loss,
            "avg_reasoning_loss_per_session": avg_reasoning_loss,
        }

    def get_drift_trends(self, hours: int = 24) -> Dict[str, List]:
        """Get drift trends over time."""
        now = datetime.utcnow()
        cutoff_time = now - timedelta(hours=hours)

        relevant_sessions = [s for s in self.sessions if s.started_at >= cutoff_time]

        if not relevant_sessions:
            return {}

        # Bucket sessions by hour
        buckets = defaultdict(list)
        for session in relevant_sessions:
            bucket_time = session.started_at.replace(minute=0, second=0, microsecond=0)
            bucket_key = bucket_time.isoformat()
            buckets[bucket_key].append(session)

        trends = {}
        for bucket_key in sorted(buckets.keys()):
            sessions_in_bucket = buckets[bucket_key]
            avg_degradation = (
                sum(s.total_degradation for s in sessions_in_bucket)
                / len(sessions_in_bucket)
                if sessions_in_bucket
                else 0
            )
            max_drift_level = max(
                (s.max_drift_level.value for s in sessions_in_bucket),
                key=lambda x: [
                    "stable",
                    "minor",
                    "moderate",
                    "significant",
                    "critical",
                ].index(x),
            )

            if "degradation_trend" not in trends:
                trends["degradation_trend"] = []
            if "drift_level_trend" not in trends:
                trends["drift_level_trend"] = []

            trends["degradation_trend"].append(
                {"timestamp": bucket_key, "avg_degradation": avg_degradation}
            )
            trends["drift_level_trend"].append(
                {"timestamp": bucket_key, "max_drift_level": max_drift_level}
            )

        return trends

    def detect_regression(
        self, session_id: str, threshold_percentage: float = 10.0
    ) -> bool:
        """
        Detect if a session shows regression in semantic quality.

        Args:
            session_id: Session to check
            threshold_percentage: Degradation threshold for regression

        Returns:
            True if degradation exceeds threshold
        """
        session = self.get_session(session_id)
        if not session:
            return False

        return session.total_degradation > threshold_percentage

    def get_provider_drift_comparison(self) -> Dict[str, Dict]:
        """Compare semantic drift across providers."""
        provider_sessions = defaultdict(list)

        for session in self.sessions:
            provider_sessions[session.provider].append(session)

        comparison = {}
        for provider, sessions in provider_sessions.items():
            if sessions:
                avg_degradation = sum(s.total_degradation for s in sessions) / len(
                    sessions
                )
                max_drift_level = max(
                    (s.max_drift_level for s in sessions),
                    key=lambda x: [
                        DriftLevel.STABLE,
                        DriftLevel.MINOR,
                        DriftLevel.MODERATE,
                        DriftLevel.SIGNIFICANT,
                        DriftLevel.CRITICAL,
                    ].index(x),
                )

                comparison[provider] = {
                    "sessions": len(sessions),
                    "avg_degradation_percentage": avg_degradation,
                    "max_drift_level": max_drift_level.value,
                    "total_entity_loss": sum(
                        s.cumulative_entity_loss for s in sessions
                    ),
                    "total_reasoning_loss": sum(
                        s.cumulative_reasoning_loss for s in sessions
                    ),
                }

        return comparison

    def get_drift_analyzer_report(self) -> Dict:
        """Generate comprehensive drift analysis report."""
        if not self.sessions:
            return {"message": "No drift sessions recorded"}

        return {
            "statistics": self.get_drift_statistics(lookback_sessions=1000),
            "trends": self.get_drift_trends(hours=24),
            "provider_comparison": self.get_provider_drift_comparison(),
        }

    def export_sessions(self, output_file: str) -> str:
        """Export drift sessions to JSON file."""
        report = {
            "exported_at": datetime.utcnow().isoformat(),
            "total_sessions": len(self.sessions),
            "sessions": [s.to_dict() for s in self.sessions[-500:]],  # Last 500
            "report": self.get_drift_analyzer_report(),
        }

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Exported drift sessions to {output_file}")
        return output_file


# Global semantic drift analyzer instance
_drift_analyzer: Optional[SemanticDriftAnalyzer] = None


def get_drift_analyzer() -> SemanticDriftAnalyzer:
    """Get or create the global semantic drift analyzer."""
    global _drift_analyzer
    if _drift_analyzer is None:
        _drift_analyzer = SemanticDriftAnalyzer()
    return _drift_analyzer
