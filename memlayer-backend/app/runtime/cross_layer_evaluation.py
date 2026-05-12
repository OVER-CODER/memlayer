"""
Cross-layer runtime evaluation and optimization tooling for Phase 6.5.

This module validates emergent behavior across:
workspace state -> adaptive runtime -> view compiler -> replay -> diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import json
import re

from app.view_engine import (
    CompiledSemanticView,
    ViewEngineCompiler,
    ViewReplayEngine,
    ViewType,
    WorkspaceSemanticState,
)


@dataclass
class SemanticFidelityReport:
    semantic_preservation: float
    reasoning_continuity: float
    entity_preservation: float
    context_integrity: float
    degradation_index: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "semantic_preservation": self.semantic_preservation,
            "reasoning_continuity": self.reasoning_continuity,
            "entity_preservation": self.entity_preservation,
            "context_integrity": self.context_integrity,
            "degradation_index": self.degradation_index,
        }


@dataclass
class CrossViewConsistencyReport:
    avg_overlap: float
    avg_divergence: float
    overlap_matrix: Dict[str, Dict[str, float]]
    divergence_matrix: Dict[str, Dict[str, float]]
    over_divergence_detected: bool
    over_redundancy_detected: bool
    context_fragmentation_risk: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "avg_overlap": self.avg_overlap,
            "avg_divergence": self.avg_divergence,
            "overlap_matrix": self.overlap_matrix,
            "divergence_matrix": self.divergence_matrix,
            "over_divergence_detected": self.over_divergence_detected,
            "over_redundancy_detected": self.over_redundancy_detected,
            "context_fragmentation_risk": self.context_fragmentation_risk,
        }


@dataclass
class ReplayIntegrityReport:
    total_checks: int
    deterministic_matches: int
    deterministic_mismatches: int
    determinism_rate: float
    provider_breakdown: Dict[str, Dict[str, float]]
    drift_alerts: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_checks": self.total_checks,
            "deterministic_matches": self.deterministic_matches,
            "deterministic_mismatches": self.deterministic_mismatches,
            "determinism_rate": self.determinism_rate,
            "provider_breakdown": self.provider_breakdown,
            "drift_alerts": self.drift_alerts,
        }


@dataclass
class ProjectionEvolutionReport:
    timeline: List[Dict[str, Any]]
    avg_drift: float
    max_drift: float
    semantic_erosion: float
    token_efficiency_evolution: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timeline": self.timeline,
            "avg_drift": self.avg_drift,
            "max_drift": self.max_drift,
            "semantic_erosion": self.semantic_erosion,
            "token_efficiency_evolution": self.token_efficiency_evolution,
        }


@dataclass
class TokenEconomicsReport:
    avg_token_budget_used: float
    avg_projection_tokens: float
    semantic_value_per_token: float
    provider_token_efficiency: Dict[str, float]
    view_token_efficiency: Dict[str, float]
    redundant_projection_overhead: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "avg_token_budget_used": self.avg_token_budget_used,
            "avg_projection_tokens": self.avg_projection_tokens,
            "semantic_value_per_token": self.semantic_value_per_token,
            "provider_token_efficiency": self.provider_token_efficiency,
            "view_token_efficiency": self.view_token_efficiency,
            "redundant_projection_overhead": self.redundant_projection_overhead,
        }


@dataclass
class ProviderDivergenceReport:
    divergence_by_view: Dict[str, float]
    quality_spread_by_provider: Dict[str, float]
    robustness_ranking: List[Tuple[str, float]]
    adaptation_heatmap: Dict[str, Dict[str, float]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "divergence_by_view": self.divergence_by_view,
            "quality_spread_by_provider": self.quality_spread_by_provider,
            "robustness_ranking": [
                {"provider": provider, "score": score}
                for provider, score in self.robustness_ranking
            ],
            "adaptation_heatmap": self.adaptation_heatmap,
        }


@dataclass
class CrossLayerEvaluationReport:
    report_id: str
    workspace_id: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    providers_evaluated: List[str] = field(default_factory=list)
    view_count: int = 0
    semantic_fidelity: Optional[SemanticFidelityReport] = None
    cross_view_consistency: Optional[CrossViewConsistencyReport] = None
    replay_integrity: Optional[ReplayIntegrityReport] = None
    projection_evolution: Optional[ProjectionEvolutionReport] = None
    token_economics: Optional[TokenEconomicsReport] = None
    provider_divergence: Optional[ProviderDivergenceReport] = None
    optimization_recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "workspace_id": self.workspace_id,
            "generated_at": self.generated_at.isoformat(),
            "providers_evaluated": self.providers_evaluated,
            "view_count": self.view_count,
            "semantic_fidelity": (
                self.semantic_fidelity.to_dict() if self.semantic_fidelity else None
            ),
            "cross_view_consistency": (
                self.cross_view_consistency.to_dict()
                if self.cross_view_consistency
                else None
            ),
            "replay_integrity": (
                self.replay_integrity.to_dict() if self.replay_integrity else None
            ),
            "projection_evolution": (
                self.projection_evolution.to_dict()
                if self.projection_evolution
                else None
            ),
            "token_economics": (
                self.token_economics.to_dict() if self.token_economics else None
            ),
            "provider_divergence": (
                self.provider_divergence.to_dict()
                if self.provider_divergence
                else None
            ),
            "optimization_recommendations": self.optimization_recommendations,
        }


class CrossLayerEvaluationFramework:
    """
    End-to-end cross-layer evaluator for runtime + view virtualization systems.

    The framework is deterministic by design and keeps historical reports for
    longitudinal stability analysis.
    """

    def __init__(
        self,
        view_compiler: ViewEngineCompiler,
        view_replay_engine: Optional[ViewReplayEngine] = None,
        max_reports: int = 1000,
    ):
        self.view_compiler = view_compiler
        self.view_replay_engine = view_replay_engine or ViewReplayEngine(view_compiler)
        self.max_reports = max_reports
        self.reports: List[CrossLayerEvaluationReport] = []

    def evaluate_runtime_stack(
        self,
        semantic_state: WorkspaceSemanticState,
        providers: Optional[List[str]] = None,
        replay_cycles: int = 3,
        evolution_steps: int = 6,
        report_id: Optional[str] = None,
    ) -> CrossLayerEvaluationReport:
        """
        Evaluate the complete runtime stack end-to-end.
        """
        provider_list = providers or [semantic_state.provider]
        all_compiled: Dict[str, Dict[str, CompiledSemanticView]] = {}
        flattened: List[CompiledSemanticView] = []

        for provider in provider_list:
            compiled = self.view_compiler.compile_all_views(
                semantic_state=semantic_state,
                provider=provider,
            )
            all_compiled[provider] = compiled
            flattened.extend(compiled.values())

        semantic_fidelity = self._evaluate_semantic_fidelity(
            semantic_state=semantic_state,
            compiled_views=flattened,
        )
        cross_view_consistency = self._evaluate_cross_view_consistency(
            compiled_by_provider=all_compiled
        )
        replay_integrity = self._evaluate_replay_integrity(
            semantic_state=semantic_state,
            providers=provider_list,
            cycles=max(1, replay_cycles),
        )
        projection_evolution = self._evaluate_projection_evolution(
            semantic_state=semantic_state,
            providers=provider_list,
            steps=max(2, evolution_steps),
        )
        token_economics = self._evaluate_token_economics(flattened)
        provider_divergence = self._evaluate_provider_divergence(
            compiled_by_provider=all_compiled,
            replay_integrity=replay_integrity,
        )

        recommendations = self._generate_optimization_recommendations(
            semantic_fidelity=semantic_fidelity,
            consistency=cross_view_consistency,
            replay=replay_integrity,
            economics=token_economics,
            divergence=provider_divergence,
            evolution=projection_evolution,
        )

        resolved_report_id = report_id or f"xlayer-{semantic_state.workspace_id}-{len(self.reports)+1:04d}"
        report = CrossLayerEvaluationReport(
            report_id=resolved_report_id,
            workspace_id=semantic_state.workspace_id,
            providers_evaluated=provider_list,
            view_count=len(flattened),
            semantic_fidelity=semantic_fidelity,
            cross_view_consistency=cross_view_consistency,
            replay_integrity=replay_integrity,
            projection_evolution=projection_evolution,
            token_economics=token_economics,
            provider_divergence=provider_divergence,
            optimization_recommendations=recommendations,
        )

        self.reports.append(report)
        if len(self.reports) > self.max_reports:
            self.reports = self.reports[-self.max_reports :]
        return report

    def export_report(self, report_id: str, output_file: str) -> str:
        report = self.get_report(report_id)
        if report is None:
            raise ValueError(f"Report not found: {report_id}")
        payload = {"exported_at": datetime.now(timezone.utc).isoformat(), "report": report.to_dict()}
        with open(output_file, "w") as file_obj:
            json.dump(payload, file_obj, indent=2)
        return output_file

    def export_history(self, output_file: str) -> str:
        payload = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_reports": len(self.reports),
            "reports": [report.to_dict() for report in self.reports],
            "latest_summary": self.get_latest_summary(),
        }
        with open(output_file, "w") as file_obj:
            json.dump(payload, file_obj, indent=2)
        return output_file

    def get_report(self, report_id: str) -> Optional[CrossLayerEvaluationReport]:
        for report in self.reports:
            if report.report_id == report_id:
                return report
        return None

    def get_latest_summary(self) -> Dict[str, Any]:
        if not self.reports:
            return {"message": "No cross-layer reports available"}

        latest = self.reports[-1]
        replay = latest.replay_integrity
        divergence = latest.provider_divergence
        fidelity = latest.semantic_fidelity

        return {
            "latest_report_id": latest.report_id,
            "generated_at": latest.generated_at.isoformat(),
            "workspace_id": latest.workspace_id,
            "providers_evaluated": latest.providers_evaluated,
            "semantic_preservation": fidelity.semantic_preservation if fidelity else 0.0,
            "determinism_rate": replay.determinism_rate if replay else 0.0,
            "avg_view_divergence": (
                latest.cross_view_consistency.avg_divergence
                if latest.cross_view_consistency
                else 0.0
            ),
            "provider_robustness_ranking": (
                divergence.to_dict()["robustness_ranking"] if divergence else []
            ),
            "recommendations": latest.optimization_recommendations,
        }

    def _evaluate_semantic_fidelity(
        self,
        semantic_state: WorkspaceSemanticState,
        compiled_views: List[CompiledSemanticView],
    ) -> SemanticFidelityReport:
        if not compiled_views:
            return SemanticFidelityReport(0.0, 0.0, 0.0, 0.0, 1.0)

        semantic_preservation = self._average(
            [view.quality_report.semantic_preservation for view in compiled_views]
        )
        reasoning_continuity = self._average(
            [view.quality_report.reasoning_continuity for view in compiled_views]
        )
        context_integrity = self._average(
            [view.quality_report.semantic_overlap_with_base for view in compiled_views]
        )

        source_entities = self._extract_entities(
            " ".join(str(getattr(memory, "raw_content", str(memory))) for memory in semantic_state.memories)
        )
        projection_entities = self._extract_entities(
            " ".join(view.projection.compiled_context for view in compiled_views)
        )
        if not source_entities:
            entity_preservation = 1.0
        else:
            entity_preservation = len(source_entities.intersection(projection_entities)) / len(source_entities)

        degradation_index = max(
            0.0,
            min(
                1.0,
                1.0
                - (
                    semantic_preservation * 0.45
                    + reasoning_continuity * 0.25
                    + entity_preservation * 0.15
                    + context_integrity * 0.15
                ),
            ),
        )

        return SemanticFidelityReport(
            semantic_preservation=semantic_preservation,
            reasoning_continuity=reasoning_continuity,
            entity_preservation=entity_preservation,
            context_integrity=context_integrity,
            degradation_index=degradation_index,
        )

    def _evaluate_cross_view_consistency(
        self,
        compiled_by_provider: Dict[str, Dict[str, CompiledSemanticView]],
    ) -> CrossViewConsistencyReport:
        overlap_matrix: Dict[str, Dict[str, float]] = {}
        divergence_matrix: Dict[str, Dict[str, float]] = {}
        pairwise_overlaps: List[float] = []
        pairwise_divergences: List[float] = []

        for provider, compiled in compiled_by_provider.items():
            views = list(compiled.values())
            if len(views) < 2:
                continue

            comparison = self.view_compiler.compare_compiled_views(views)
            pairwise = comparison["projection_report"]["pairwise_comparisons"]
            for item in pairwise:
                key_a = f"{provider}:{item['projection_a']}"
                key_b = f"{provider}:{item['projection_b']}"
                overlap = float(item["jaccard_overlap"])
                divergence = float(item["semantic_divergence"])
                pairwise_overlaps.append(overlap)
                pairwise_divergences.append(divergence)

                overlap_matrix.setdefault(key_a, {})[key_b] = overlap
                overlap_matrix.setdefault(key_b, {})[key_a] = overlap
                divergence_matrix.setdefault(key_a, {})[key_b] = divergence
                divergence_matrix.setdefault(key_b, {})[key_a] = divergence

        avg_overlap = self._average(pairwise_overlaps, default=1.0)
        avg_divergence = self._average(pairwise_divergences, default=0.0)

        return CrossViewConsistencyReport(
            avg_overlap=avg_overlap,
            avg_divergence=avg_divergence,
            overlap_matrix=overlap_matrix,
            divergence_matrix=divergence_matrix,
            over_divergence_detected=avg_divergence > 0.70,
            over_redundancy_detected=avg_overlap > 0.90,
            context_fragmentation_risk=max(0.0, min(1.0, avg_divergence - 0.35)),
        )

    def _evaluate_replay_integrity(
        self,
        semantic_state: WorkspaceSemanticState,
        providers: List[str],
        cycles: int,
    ) -> ReplayIntegrityReport:
        breakdown: Dict[str, Dict[str, float]] = {}
        total_checks = 0
        deterministic_matches = 0
        drift_alerts: List[str] = []

        for provider in providers:
            provider_checks = 0
            provider_matches = 0
            for view_type in [
                ViewType.RESEARCH,
                ViewType.DRAFTER,
                ViewType.TOOL_AGENT,
                ViewType.CRITIC,
            ]:
                for _ in range(cycles):
                    replay = self.view_replay_engine.replay_view(
                        semantic_state=semantic_state,
                        view_type=view_type,
                        provider=provider,
                    )
                    deterministic = bool(replay["deterministic_match"])
                    provider_checks += 1
                    total_checks += 1
                    if deterministic:
                        provider_matches += 1
                        deterministic_matches += 1
                    else:
                        drift_alerts.append(
                            f"nondeterministic:{provider}:{view_type.value}:"
                            f"{replay['replay_trace']['replay_trace_id']}"
                        )

            mismatch = provider_checks - provider_matches
            breakdown[provider] = {
                "total_checks": provider_checks,
                "matches": provider_matches,
                "mismatches": mismatch,
                "determinism_rate": (
                    provider_matches / provider_checks if provider_checks else 1.0
                ),
            }

        deterministic_mismatches = total_checks - deterministic_matches
        determinism_rate = (
            deterministic_matches / total_checks if total_checks else 1.0
        )
        return ReplayIntegrityReport(
            total_checks=total_checks,
            deterministic_matches=deterministic_matches,
            deterministic_mismatches=deterministic_mismatches,
            determinism_rate=determinism_rate,
            provider_breakdown=breakdown,
            drift_alerts=drift_alerts,
        )

    def _evaluate_projection_evolution(
        self,
        semantic_state: WorkspaceSemanticState,
        providers: List[str],
        steps: int,
    ) -> ProjectionEvolutionReport:
        timeline: List[Dict[str, Any]] = []
        drifts: List[float] = []
        efficiency_points: Dict[str, List[float]] = {}

        previous_by_provider_view: Dict[Tuple[str, str], CompiledSemanticView] = {}
        first_quality: Optional[float] = None
        last_quality: Optional[float] = None

        for step in range(steps):
            step_state = WorkspaceSemanticState(
                workspace_id=semantic_state.workspace_id,
                query=f"{semantic_state.query} [evolution_step={step}]",
                memories=semantic_state.memories,
                provider=semantic_state.provider,
                token_budget=semantic_state.token_budget,
                query_type=semantic_state.query_type,
                original_context=semantic_state.original_context,
                workspace_state=semantic_state.workspace_state,
                metadata={**semantic_state.metadata, "evolution_step": step},
            )

            for provider in providers:
                compiled = self.view_compiler.compile_all_views(step_state, provider=provider)
                for view_name, view in compiled.items():
                    key = (provider, view_name)
                    efficiency_points.setdefault(provider, []).append(
                        view.quality_report.token_efficiency
                    )

                    prev = previous_by_provider_view.get(key)
                    drift = 0.0
                    if prev is not None:
                        comparison = self.view_compiler.projection_engine.compare_projections(
                            prev.projection,
                            view.projection,
                        )
                        drift = float(comparison["semantic_divergence"])
                        drifts.append(drift)

                    previous_by_provider_view[key] = view
                    timeline.append(
                        {
                            "step": step,
                            "provider": provider,
                            "view_type": view_name,
                            "quality": view.quality_report.overall_quality(),
                            "token_efficiency": view.quality_report.token_efficiency,
                            "projection_checksum": view.projection.projection_checksum,
                            "drift_from_previous": drift,
                        }
                    )

                    if first_quality is None:
                        first_quality = view.quality_report.overall_quality()
                    last_quality = view.quality_report.overall_quality()

        semantic_erosion = 0.0
        if first_quality is not None and last_quality is not None:
            semantic_erosion = max(0.0, first_quality - last_quality)

        efficiency_evolution: Dict[str, float] = {}
        for provider, points in efficiency_points.items():
            if not points:
                efficiency_evolution[provider] = 0.0
                continue
            efficiency_evolution[provider] = points[-1] - points[0]

        return ProjectionEvolutionReport(
            timeline=timeline,
            avg_drift=self._average(drifts, default=0.0),
            max_drift=max(drifts) if drifts else 0.0,
            semantic_erosion=semantic_erosion,
            token_efficiency_evolution=efficiency_evolution,
        )

    def _evaluate_token_economics(
        self, compiled_views: List[CompiledSemanticView]
    ) -> TokenEconomicsReport:
        if not compiled_views:
            return TokenEconomicsReport(0.0, 0.0, 0.0, {}, {}, 0.0)

        budgets = [view.metrics.token_budget_used for view in compiled_views]
        projection_tokens = [
            len(view.projection.compiled_context.split()) for view in compiled_views
        ]
        qualities = [view.quality_report.overall_quality() for view in compiled_views]

        provider_token_efficiency: Dict[str, float] = {}
        view_token_efficiency: Dict[str, float] = {}

        providers = sorted({view.provider for view in compiled_views})
        for provider in providers:
            provider_views = [view for view in compiled_views if view.provider == provider]
            provider_token_efficiency[provider] = self._average(
                [view.quality_report.token_efficiency for view in provider_views]
            )

        for view_type in [view_type.value for view_type in ViewType]:
            typed = [view for view in compiled_views if view.view_type.value == view_type]
            view_token_efficiency[view_type] = self._average(
                [view.quality_report.token_efficiency for view in typed],
                default=0.0,
            )

        all_tokens = re.findall(
            r"[A-Za-z0-9_]+",
            " ".join(view.projection.compiled_context for view in compiled_views).lower(),
        )
        unique_ratio = (len(set(all_tokens)) / len(all_tokens)) if all_tokens else 1.0
        redundant_projection_overhead = max(0.0, 1.0 - unique_ratio)

        total_projection_tokens = sum(projection_tokens)
        semantic_value_per_token = (
            sum(qualities) / total_projection_tokens if total_projection_tokens else 0.0
        )

        return TokenEconomicsReport(
            avg_token_budget_used=self._average([float(item) for item in budgets]),
            avg_projection_tokens=self._average([float(item) for item in projection_tokens]),
            semantic_value_per_token=semantic_value_per_token,
            provider_token_efficiency=provider_token_efficiency,
            view_token_efficiency=view_token_efficiency,
            redundant_projection_overhead=redundant_projection_overhead,
        )

    def _evaluate_provider_divergence(
        self,
        compiled_by_provider: Dict[str, Dict[str, CompiledSemanticView]],
        replay_integrity: ReplayIntegrityReport,
    ) -> ProviderDivergenceReport:
        providers = list(compiled_by_provider.keys())
        divergence_by_view: Dict[str, float] = {}
        adaptation_heatmap: Dict[str, Dict[str, float]] = {}
        quality_spread_by_provider: Dict[str, float] = {}

        for provider, views in compiled_by_provider.items():
            qualities = [view.quality_report.overall_quality() for view in views.values()]
            if qualities:
                quality_spread_by_provider[provider] = max(qualities) - min(qualities)
            else:
                quality_spread_by_provider[provider] = 0.0

            adaptation_heatmap[provider] = {
                view_name: view.quality_report.specialization_effectiveness
                for view_name, view in views.items()
            }

        for view_name in [view.value for view in ViewType]:
            quality_points: List[float] = []
            for provider in providers:
                view = compiled_by_provider.get(provider, {}).get(view_name)
                if view is not None:
                    quality_points.append(view.quality_report.overall_quality())
            divergence_by_view[view_name] = (
                max(quality_points) - min(quality_points) if quality_points else 0.0
            )

        ranking: List[Tuple[str, float]] = []
        for provider in providers:
            provider_views = compiled_by_provider.get(provider, {})
            avg_quality = self._average(
                [view.quality_report.overall_quality() for view in provider_views.values()],
                default=0.0,
            )
            determinism = replay_integrity.provider_breakdown.get(provider, {}).get(
                "determinism_rate", 1.0
            )
            score = avg_quality * 0.7 + determinism * 0.3
            ranking.append((provider, score))

        ranking.sort(key=lambda item: item[1], reverse=True)

        return ProviderDivergenceReport(
            divergence_by_view=divergence_by_view,
            quality_spread_by_provider=quality_spread_by_provider,
            robustness_ranking=ranking,
            adaptation_heatmap=adaptation_heatmap,
        )

    def _generate_optimization_recommendations(
        self,
        semantic_fidelity: SemanticFidelityReport,
        consistency: CrossViewConsistencyReport,
        replay: ReplayIntegrityReport,
        economics: TokenEconomicsReport,
        divergence: ProviderDivergenceReport,
        evolution: ProjectionEvolutionReport,
    ) -> List[str]:
        recs: List[str] = []

        if semantic_fidelity.degradation_index > 0.25:
            recs.append("Increase preservation bias for high-risk projections to reduce semantic degradation.")
        if consistency.over_divergence_detected:
            recs.append("Tighten cross-view overlap floor to avoid context fragmentation across specialized views.")
        if consistency.over_redundancy_detected:
            recs.append("Raise specialization penalties in view shaping to reduce redundant projection overlap.")
        if replay.determinism_rate < 1.0:
            recs.append("Investigate nondeterministic replay groups and enforce stable ordering/checksum inputs.")
        if economics.redundant_projection_overhead > 0.35:
            recs.append("Increase context reuse and deduplicate repeated projection segments to improve token economics.")
        if evolution.semantic_erosion > 0.10:
            recs.append("Enable conservative compression on long-horizon cycles to mitigate semantic erosion.")

        if divergence.robustness_ranking:
            weakest_provider = divergence.robustness_ranking[-1][0]
            recs.append(
                f"Run targeted provider calibration benchmarks for {weakest_provider} across all core views."
            )

        if not recs:
            recs.append("No critical optimization actions required; maintain current runtime configuration.")
        return recs

    def _extract_entities(self, text: str) -> set[str]:
        return {token for token in re.findall(r"\b[A-Z][A-Za-z0-9_]+\b", text)}

    def _average(self, values: List[float], default: float = 0.0) -> float:
        if not values:
            return default
        return sum(values) / len(values)
