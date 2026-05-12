"""
Emergent Failure Detection System for Phase 5B.

Detects runtime failures that emerge from complex interactions:
- Semantic collapse and degradation
- Entity erosion across cycles
- Retrieval poisoning
- Context fragmentation
- Recursive degradation
- Provider instability
- Adaptive allocation drift
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FailureSeverity(Enum):
    """Failure severity levels."""

    INFO = "info"  # Observable but not critical
    WARNING = "warning"  # Degradation detected
    ERROR = "error"  # Significant failure
    CRITICAL = "critical"  # System instability
    CATASTROPHIC = "catastrophic"  # Complete failure


class FailureType(Enum):
    """Types of emergent failures."""

    SEMANTIC_COLLAPSE = "semantic_collapse"
    ENTITY_EROSION = "entity_erosion"
    REASONING_CONTINUITY_LOSS = "reasoning_continuity_loss"
    RETRIEVAL_POISONING = "retrieval_poisoning"
    CONTEXT_FRAGMENTATION = "context_fragmentation"
    RECURSIVE_DEGRADATION = "recursive_degradation"
    TOKEN_EXPLOSION = "token_explosion"
    PROVIDER_INSTABILITY = "provider_instability"
    ALLOCATION_DRIFT = "allocation_drift"
    COMPRESSION_RUNAWAY = "compression_runaway"


@dataclass
class RuntimeFailure:
    """Record of an emergent runtime failure."""

    failure_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Classification
    failure_type: FailureType = FailureType.SEMANTIC_COLLAPSE
    severity: FailureSeverity = FailureSeverity.WARNING

    # Context
    query: str = ""
    provider: str = ""
    compression_mode: str = ""
    cycle_number: int = 0

    # Metrics at failure
    semantic_density: float = 0.0
    entity_preservation: float = 0.0
    reasoning_continuity: float = 0.0
    token_count: int = 0
    quality_score: float = 0.0

    # Failure indicators
    degradation_rate: float = 0.0  # % degradation from previous cycle
    time_to_failure: float = 0.0  # ms
    propagation_depth: int = 0  # How many stages affected

    # Recovery information
    auto_recovery_attempted: bool = False
    recovery_successful: bool = False

    # Description
    description: str = ""
    mitigation_suggestion: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "failure_id": self.failure_id,
            "timestamp": self.timestamp.isoformat(),
            "failure_type": self.failure_type.value,
            "severity": self.severity.value,
            "query": self.query[:100],
            "provider": self.provider,
            "compression_mode": self.compression_mode,
            "cycle_number": self.cycle_number,
            "semantic_density": self.semantic_density,
            "entity_preservation": self.entity_preservation,
            "reasoning_continuity": self.reasoning_continuity,
            "token_count": self.token_count,
            "quality_score": self.quality_score,
            "degradation_rate": self.degradation_rate,
            "time_to_failure": self.time_to_failure,
            "propagation_depth": self.propagation_depth,
            "auto_recovery_attempted": self.auto_recovery_attempted,
            "recovery_successful": self.recovery_successful,
            "description": self.description,
            "mitigation_suggestion": self.mitigation_suggestion,
        }


@dataclass
class FailurePattern:
    """Detected pattern of repeated failures."""

    pattern_id: str
    failure_type: FailureType
    occurrence_count: int = 0

    # Triggering conditions
    triggered_by_provider: Optional[str] = None
    triggered_by_compression_mode: Optional[str] = None
    triggered_by_cycle_count: Optional[int] = None

    # Pattern metrics
    avg_degradation_rate: float = 0.0
    avg_time_to_failure: float = 0.0
    avg_severity: str = "warning"

    # Recovery rate
    recovery_rate: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "failure_type": self.failure_type.value,
            "occurrence_count": self.occurrence_count,
            "triggered_by_provider": self.triggered_by_provider,
            "triggered_by_compression_mode": self.triggered_by_compression_mode,
            "triggered_by_cycle_count": self.triggered_by_cycle_count,
            "avg_degradation_rate": self.avg_degradation_rate,
            "avg_time_to_failure": self.avg_time_to_failure,
            "avg_severity": self.avg_severity,
            "recovery_rate": self.recovery_rate,
        }


class EmergentFailureDetector:
    """
    Detects emergent failures in runtime execution.

    Monitors for:
    - Semantic collapse and degradation patterns
    - Entity erosion across compression cycles
    - Reasoning continuity loss
    - Retrieval poisoning
    - Context fragmentation
    - Token explosion
    - Provider instability
    - Allocation drift
    """

    def __init__(self, max_failures: int = 10000):
        """
        Initialize failure detector.

        Args:
            max_failures: Maximum failures to track
        """
        self.max_failures = max_failures
        self.failures: List[RuntimeFailure] = []
        self.patterns: Dict[str, FailurePattern] = {}

        logger.info("Emergent Failure Detector initialized")

    def detect_semantic_collapse(
        self,
        failure_id: str,
        query: str,
        provider: str,
        compression_mode: str,
        current_semantic_density: float,
        previous_semantic_density: float,
        cycle_number: int = 0,
    ) -> Optional[RuntimeFailure]:
        """Detect semantic collapse (rapid quality degradation)."""
        degradation_rate = (
            (previous_semantic_density - current_semantic_density)
            / previous_semantic_density
            if previous_semantic_density > 0
            else 0.0
        )

        # Semantic collapse: > 20% degradation in single cycle
        if degradation_rate > 0.20:
            severity = (
                FailureSeverity.CATASTROPHIC
                if degradation_rate > 0.50
                else FailureSeverity.CRITICAL
                if degradation_rate > 0.35
                else FailureSeverity.ERROR
            )

            failure = RuntimeFailure(
                failure_id=failure_id,
                failure_type=FailureType.SEMANTIC_COLLAPSE,
                severity=severity,
                query=query,
                provider=provider,
                compression_mode=compression_mode,
                cycle_number=cycle_number,
                semantic_density=current_semantic_density,
                degradation_rate=degradation_rate * 100,
                description=f"Semantic collapse detected: {degradation_rate * 100:.1f}% degradation",
                mitigation_suggestion="Reduce compression aggressiveness or increase token budget",
            )

            self._store_failure(failure)
            return failure

        return None

    def detect_entity_erosion(
        self,
        failure_id: str,
        query: str,
        provider: str,
        previous_entity_count: int,
        current_entity_count: int,
        current_preservation_ratio: float,
        cycle_number: int = 0,
    ) -> Optional[RuntimeFailure]:
        """Detect entity erosion across compression cycles."""
        entity_loss_rate = (
            (previous_entity_count - current_entity_count) / previous_entity_count
            if previous_entity_count > 0
            else 0.0
        )

        # Entity erosion: > 15% loss per cycle
        if entity_loss_rate > 0.15 and current_preservation_ratio < 0.75:
            severity = (
                FailureSeverity.ERROR
                if entity_loss_rate > 0.30
                else FailureSeverity.WARNING
            )

            failure = RuntimeFailure(
                failure_id=failure_id,
                failure_type=FailureType.ENTITY_EROSION,
                severity=severity,
                query=query,
                provider=provider,
                cycle_number=cycle_number,
                entity_preservation=current_preservation_ratio,
                degradation_rate=entity_loss_rate * 100,
                description=f"Entity erosion: {current_entity_count}/{previous_entity_count} preserved",
                mitigation_suggestion="Implement entity anchoring or reduce compression ratio",
            )

            self._store_failure(failure)
            return failure

        return None

    def detect_reasoning_continuity_loss(
        self,
        failure_id: str,
        query: str,
        provider: str,
        previous_continuity: float,
        current_continuity: float,
        cycle_number: int = 0,
    ) -> Optional[RuntimeFailure]:
        """Detect loss of reasoning chain continuity."""
        continuity_loss = (
            (previous_continuity - current_continuity) / previous_continuity
            if previous_continuity > 0
            else 0.0
        )

        # Continuity loss: > 10% per cycle
        if continuity_loss > 0.10 and current_continuity < 0.80:
            severity = (
                FailureSeverity.ERROR
                if continuity_loss > 0.25
                else FailureSeverity.WARNING
            )

            failure = RuntimeFailure(
                failure_id=failure_id,
                failure_type=FailureType.REASONING_CONTINUITY_LOSS,
                severity=severity,
                query=query,
                provider=provider,
                reasoning_continuity=current_continuity,
                degradation_rate=continuity_loss * 100,
                cycle_number=cycle_number,
                description=f"Reasoning continuity loss: {current_continuity:.2f}",
                mitigation_suggestion="Preserve reasoning context layer or reduce chunking",
            )

            self._store_failure(failure)
            return failure

        return None

    def detect_token_explosion(
        self,
        failure_id: str,
        query: str,
        provider: str,
        previous_token_count: int,
        current_token_count: int,
        token_budget: int,
        cycle_number: int = 0,
    ) -> Optional[RuntimeFailure]:
        """Detect runaway token growth."""
        token_growth_rate = (
            (current_token_count - previous_token_count) / previous_token_count
            if previous_token_count > 0
            else 0.0
        )

        # Token explosion: > 50% growth or exceeding budget
        if token_growth_rate > 0.50 or current_token_count > token_budget:
            severity = (
                FailureSeverity.CRITICAL
                if current_token_count > token_budget * 1.5
                else FailureSeverity.ERROR
            )

            failure = RuntimeFailure(
                failure_id=failure_id,
                failure_type=FailureType.TOKEN_EXPLOSION,
                severity=severity,
                query=query,
                provider=provider,
                token_count=current_token_count,
                degradation_rate=token_growth_rate * 100,
                cycle_number=cycle_number,
                description=f"Token explosion: {current_token_count} tokens "
                f"({token_growth_rate * 100:.1f}% growth)",
                mitigation_suggestion="Increase compression aggressiveness or reduce memory scope",
            )

            self._store_failure(failure)
            return failure

        return None

    def detect_provider_instability(
        self,
        failure_id: str,
        provider: str,
        query_type: str,
        quality_scores: List[float],
    ) -> Optional[RuntimeFailure]:
        """Detect provider-specific instability."""
        if len(quality_scores) < 3:
            return None

        # Calculate variance in quality scores
        mean_quality = sum(quality_scores) / len(quality_scores)
        variance = sum((q - mean_quality) ** 2 for q in quality_scores) / len(
            quality_scores
        )
        std_dev = variance**0.5

        # High variance: > 0.2 std dev in quality
        if std_dev > 0.20:
            severity = (
                FailureSeverity.ERROR if std_dev > 0.35 else FailureSeverity.WARNING
            )

            failure = RuntimeFailure(
                failure_id=failure_id,
                failure_type=FailureType.PROVIDER_INSTABILITY,
                severity=severity,
                provider=provider,
                quality_score=mean_quality,
                degradation_rate=std_dev * 100,
                description=f"Provider instability: {std_dev:.3f} std dev in quality scores",
                mitigation_suggestion="Implement quality validation gates or provider fallback",
            )

            self._store_failure(failure)
            return failure

        return None

    def detect_allocation_drift(
        self,
        failure_id: str,
        query: str,
        provider: str,
        planned_allocation: Dict[str, int],
        actual_allocation: Dict[str, int],
        cycle_number: int = 0,
    ) -> Optional[RuntimeFailure]:
        """Detect adaptive allocation drift."""
        total_planned = sum(planned_allocation.values())
        total_actual = sum(actual_allocation.values())

        drift_layers = []
        for layer in planned_allocation:
            planned = planned_allocation.get(layer, 0)
            actual = actual_allocation.get(layer, 0)

            if planned > 0:
                drift = abs(actual - planned) / planned
                if drift > 0.25:  # > 25% deviation
                    drift_layers.append((layer, drift))

        if drift_layers:
            avg_drift = sum(d for _, d in drift_layers) / len(drift_layers)
            severity = (
                FailureSeverity.ERROR if avg_drift > 0.50 else FailureSeverity.WARNING
            )

            failure = RuntimeFailure(
                failure_id=failure_id,
                failure_type=FailureType.ALLOCATION_DRIFT,
                severity=severity,
                query=query,
                provider=provider,
                degradation_rate=avg_drift * 100,
                cycle_number=cycle_number,
                description=f"Allocation drift in {len(drift_layers)} layers: {avg_drift * 100:.1f}% avg",
                mitigation_suggestion="Review adaptive allocation logic or use fixed allocations",
            )

            self._store_failure(failure)
            return failure

        return None

    def _store_failure(self, failure: RuntimeFailure) -> None:
        """Store failure and update patterns."""
        self.failures.append(failure)

        # Trim history
        if len(self.failures) > self.max_failures:
            self.failures = self.failures[-self.max_failures :]

        # Update patterns
        pattern_key = failure.failure_type.value
        if pattern_key not in self.patterns:
            self.patterns[pattern_key] = FailurePattern(
                pattern_id=f"pattern-{pattern_key}",
                failure_type=failure.failure_type,
            )

        pattern = self.patterns[pattern_key]
        pattern.occurrence_count += 1
        pattern.avg_degradation_rate = (
            pattern.avg_degradation_rate * 0.9 + failure.degradation_rate * 0.1
        )
        pattern.avg_time_to_failure = (
            pattern.avg_time_to_failure * 0.9 + failure.time_to_failure * 0.1
        )

        logger.warning(
            f"[FAILURE] {failure.failure_type.value} detected: "
            f"{failure.description} (severity: {failure.severity.value})"
        )

    def get_failure_report(self, lookback_failures: Optional[int] = None) -> Dict:
        """Get comprehensive failure report."""
        failures = (
            self.failures[-lookback_failures:] if lookback_failures else self.failures
        )

        if not failures:
            return {"message": "No failures recorded"}

        # Group by severity
        by_severity = {}
        for failure in failures:
            severity = failure.severity.value
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(failure)

        # Group by type
        by_type = {}
        for failure in failures:
            ftype = failure.failure_type.value
            if ftype not in by_type:
                by_type[ftype] = []
            by_type[ftype].append(failure)

        return {
            "total_failures": len(failures),
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "by_type": {k: len(v) for k, v in by_type.items()},
            "failure_patterns": [p.to_dict() for p in self.patterns.values()],
            "recent_failures": [f.to_dict() for f in failures[-10:]],
        }

    def export_failures(self, output_file: str) -> str:
        """Export all failures to JSON."""
        report = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_failures": len(self.failures),
            "failures": [f.to_dict() for f in self.failures[-500:]],
            "report": self.get_failure_report(),
        }

        import json

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Failure report exported to {output_file}")
        return output_file


# Global failure detector instance
_failure_detector: Optional[EmergentFailureDetector] = None


def get_failure_detector() -> EmergentFailureDetector:
    """Get or create the global failure detector."""
    global _failure_detector
    if _failure_detector is None:
        _failure_detector = EmergentFailureDetector()
    return _failure_detector
