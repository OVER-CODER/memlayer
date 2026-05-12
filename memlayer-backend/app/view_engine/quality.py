"""Quality evaluation for semantic view projections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any
import re

from app.view_engine.definitions import ViewDefinition, ViewType
from app.view_engine.projection import SemanticProjection


@dataclass
class ViewQualityReport:
    view_type: ViewType
    provider: str
    semantic_preservation: float
    reasoning_continuity: float
    specialization_effectiveness: float
    token_efficiency: float
    projection_fidelity: float
    semantic_overlap_with_base: float
    provider_compatibility: float

    def overall_quality(self) -> float:
        return (
            self.semantic_preservation * 0.20
            + self.reasoning_continuity * 0.20
            + self.specialization_effectiveness * 0.20
            + self.token_efficiency * 0.10
            + self.projection_fidelity * 0.10
            + self.semantic_overlap_with_base * 0.10
            + self.provider_compatibility * 0.10
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "view_type": self.view_type.value,
            "provider": self.provider,
            "semantic_preservation": self.semantic_preservation,
            "reasoning_continuity": self.reasoning_continuity,
            "specialization_effectiveness": self.specialization_effectiveness,
            "token_efficiency": self.token_efficiency,
            "projection_fidelity": self.projection_fidelity,
            "semantic_overlap_with_base": self.semantic_overlap_with_base,
            "provider_compatibility": self.provider_compatibility,
            "overall_quality": self.overall_quality(),
        }


class ViewQualityEvaluator:
    """Evaluate specialized view quality and projection fidelity."""

    def evaluate(
        self,
        projection: SemanticProjection,
        base_context: str,
        view_definition: ViewDefinition,
        compiled_token_budget: int,
    ) -> ViewQualityReport:
        base_tokens = self._tokenize(base_context)
        proj_tokens = self._tokenize(projection.compiled_context)

        base_set = set(base_tokens)
        proj_set = set(proj_tokens)

        semantic_overlap = (len(base_set.intersection(proj_set)) / len(base_set)) if base_set else 1.0
        semantic_preservation = semantic_overlap

        continuity_markers = ["because", "therefore", "thus", "hence", "if", "then"]
        reasoning_continuity = self._continuity_score(projection.compiled_context, continuity_markers)

        specialization_effectiveness = self._specialization_score(
            projection.compiled_context,
            view_definition.view_type,
        )

        token_efficiency = min(1.0, (len(proj_tokens) / compiled_token_budget)) if compiled_token_budget > 0 else 0.0

        projection_fidelity = min(
            1.0,
            (semantic_preservation * 0.6 + reasoning_continuity * 0.4),
        )

        provider_profile = view_definition.resolve_provider_profile(projection.provider)
        provider_compatibility = min(
            1.0,
            (provider_profile.quality_bias + provider_profile.continuity_bias + provider_profile.compression_bias) / 3.0,
        )

        return ViewQualityReport(
            view_type=view_definition.view_type,
            provider=projection.provider,
            semantic_preservation=semantic_preservation,
            reasoning_continuity=reasoning_continuity,
            specialization_effectiveness=specialization_effectiveness,
            token_efficiency=token_efficiency,
            projection_fidelity=projection_fidelity,
            semantic_overlap_with_base=semantic_overlap,
            provider_compatibility=provider_compatibility,
        )

    def compare_quality(self, report_a: ViewQualityReport, report_b: ViewQualityReport) -> Dict[str, Any]:
        return {
            "view_a": report_a.view_type.value,
            "view_b": report_b.view_type.value,
            "overall_delta": report_a.overall_quality() - report_b.overall_quality(),
            "semantic_preservation_delta": report_a.semantic_preservation - report_b.semantic_preservation,
            "reasoning_continuity_delta": report_a.reasoning_continuity - report_b.reasoning_continuity,
            "specialization_delta": report_a.specialization_effectiveness - report_b.specialization_effectiveness,
            "token_efficiency_delta": report_a.token_efficiency - report_b.token_efficiency,
        }

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[a-zA-Z0-9_]+", text.lower())

    def _continuity_score(self, text: str, markers: list[str]) -> float:
        tokens = self._tokenize(text)
        if not tokens:
            return 0.0
        count = sum(1 for marker in markers if marker in tokens)
        return min(1.0, count / 6.0)

    def _specialization_score(self, text: str, view_type: ViewType) -> float:
        lower = text.lower()
        if view_type == ViewType.RESEARCH:
            hits = sum(
                1
                for token in ["source", "evidence", "reference", "citation", "historical"]
                if token in lower
            )
            return min(1.0, hits / 5.0)
        if view_type == ViewType.DRAFTER:
            hits = sum(1 for token in ["narrative", "flow", "coherence", "draft", "argument"] if token in lower)
            return min(1.0, hits / 5.0)
        if view_type == ViewType.TOOL_AGENT:
            hits = sum(1 for token in ["step", "api", "execute", "command", "tool"] if token in lower)
            return min(1.0, hits / 5.0)
        hits = sum(1 for token in ["contradiction", "gap", "inconsistent", "missing", "anomaly"] if token in lower)
        return min(1.0, hits / 5.0)
