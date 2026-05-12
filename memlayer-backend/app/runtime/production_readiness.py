"""Production Readiness Gate for Phase 6.5 substrate hardening.

Provides a single, deterministic boolean health signal derived from
measured cross-layer diagnostics. No heuristic drift — every threshold
is grounded in benchmark-validated signals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.runtime.cross_layer_evaluation import (
    CrossLayerEvaluationFramework,
    CrossLayerEvaluationReport,
)


@dataclass
class ReadinessThresholds:
    """Configurable thresholds for production readiness evaluation."""

    min_determinism_rate: float = 1.0
    max_degradation_index: float = 0.25
    max_semantic_erosion: float = 0.10
    max_redundant_projection_overhead: float = 0.35
    max_avg_view_divergence: float = 0.70
    min_semantic_preservation: float = 0.70
    min_providers_evaluated: int = 1
    min_view_count: int = 4


@dataclass
class ReadinessCheckResult:
    """Single check within the readiness gate."""

    name: str
    passed: bool
    measured_value: float
    threshold_value: float
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "measured_value": self.measured_value,
            "threshold_value": self.threshold_value,
            "detail": self.detail,
        }


@dataclass
class ProductionReadinessReport:
    """Aggregate production readiness signal."""

    report_id: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_production_ready: bool = False
    checks: List[ReadinessCheckResult] = field(default_factory=list)
    passed_count: int = 0
    failed_count: int = 0
    source_report_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at.isoformat(),
            "is_production_ready": self.is_production_ready,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "source_report_id": self.source_report_id,
            "checks": [c.to_dict() for c in self.checks],
        }


class ProductionReadinessGate:
    """Evaluates whether the cognition substrate is production-ready.

    All decisions are derived from CrossLayerEvaluationReport signals.
    No autonomous heuristics — only measured thresholds.
    """

    def __init__(
        self,
        cross_layer_framework: CrossLayerEvaluationFramework,
        thresholds: Optional[ReadinessThresholds] = None,
    ):
        self.framework = cross_layer_framework
        self.thresholds = thresholds or ReadinessThresholds()
        self.history: List[ProductionReadinessReport] = []

    def evaluate(
        self,
        report: Optional[CrossLayerEvaluationReport] = None,
        report_id: Optional[str] = None,
    ) -> ProductionReadinessReport:
        """Evaluate production readiness from a cross-layer report.

        If no report is given, uses the latest report from the framework.
        """
        if report is None:
            if not self.framework.reports:
                return ProductionReadinessReport(
                    report_id=report_id or "readiness-no-data",
                    is_production_ready=False,
                    checks=[
                        ReadinessCheckResult(
                            name="data_availability",
                            passed=False,
                            measured_value=0.0,
                            threshold_value=1.0,
                            detail="No cross-layer reports available.",
                        )
                    ],
                    failed_count=1,
                )
            report = self.framework.reports[-1]

        checks: List[ReadinessCheckResult] = []
        t = self.thresholds

        # 1. Determinism rate
        if report.replay_integrity:
            checks.append(ReadinessCheckResult(
                name="determinism_rate",
                passed=report.replay_integrity.determinism_rate >= t.min_determinism_rate,
                measured_value=report.replay_integrity.determinism_rate,
                threshold_value=t.min_determinism_rate,
            ))

        # 2. Degradation index
        if report.semantic_fidelity:
            checks.append(ReadinessCheckResult(
                name="degradation_index",
                passed=report.semantic_fidelity.degradation_index <= t.max_degradation_index,
                measured_value=report.semantic_fidelity.degradation_index,
                threshold_value=t.max_degradation_index,
            ))

        # 3. Semantic preservation
        if report.semantic_fidelity:
            checks.append(ReadinessCheckResult(
                name="semantic_preservation",
                passed=report.semantic_fidelity.semantic_preservation >= t.min_semantic_preservation,
                measured_value=report.semantic_fidelity.semantic_preservation,
                threshold_value=t.min_semantic_preservation,
            ))

        # 4. Semantic erosion
        if report.projection_evolution:
            checks.append(ReadinessCheckResult(
                name="semantic_erosion",
                passed=report.projection_evolution.semantic_erosion <= t.max_semantic_erosion,
                measured_value=report.projection_evolution.semantic_erosion,
                threshold_value=t.max_semantic_erosion,
            ))

        # 5. Redundant projection overhead
        if report.token_economics:
            checks.append(ReadinessCheckResult(
                name="redundant_projection_overhead",
                passed=report.token_economics.redundant_projection_overhead <= t.max_redundant_projection_overhead,
                measured_value=report.token_economics.redundant_projection_overhead,
                threshold_value=t.max_redundant_projection_overhead,
            ))

        # 6. Cross-view divergence
        if report.cross_view_consistency:
            checks.append(ReadinessCheckResult(
                name="avg_view_divergence",
                passed=report.cross_view_consistency.avg_divergence <= t.max_avg_view_divergence,
                measured_value=report.cross_view_consistency.avg_divergence,
                threshold_value=t.max_avg_view_divergence,
            ))

        # 7. Minimum coverage
        checks.append(ReadinessCheckResult(
            name="provider_coverage",
            passed=len(report.providers_evaluated) >= t.min_providers_evaluated,
            measured_value=float(len(report.providers_evaluated)),
            threshold_value=float(t.min_providers_evaluated),
        ))
        checks.append(ReadinessCheckResult(
            name="view_coverage",
            passed=report.view_count >= t.min_view_count,
            measured_value=float(report.view_count),
            threshold_value=float(t.min_view_count),
        ))

        passed = sum(1 for c in checks if c.passed)
        failed = len(checks) - passed
        is_ready = failed == 0

        resolved_id = report_id or f"readiness-{report.report_id}"
        result = ProductionReadinessReport(
            report_id=resolved_id,
            is_production_ready=is_ready,
            checks=checks,
            passed_count=passed,
            failed_count=failed,
            source_report_id=report.report_id,
        )
        self.history.append(result)
        return result

    def get_latest(self) -> Optional[ProductionReadinessReport]:
        return self.history[-1] if self.history else None
