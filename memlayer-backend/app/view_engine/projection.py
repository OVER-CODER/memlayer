"""Semantic projection engine for view-specific cognition virtualization."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Any
import hashlib
import re

from app.view_engine.definitions import ViewType, ViewDefinition


@dataclass
class SemanticProjection:
    """Single compiled semantic projection."""

    projection_id: str
    created_at: datetime
    view_type: ViewType
    provider: str
    source_trace_id: str
    compiled_context: str
    sections: Dict[str, str] = field(default_factory=dict)
    projection_checksum: str = ""

    def calculate_checksum(self) -> str:
        payload = f"{self.view_type.value}|{self.provider}|{self.compiled_context}"
        self.projection_checksum = hashlib.sha256(payload.encode()).hexdigest()[:24]
        return self.projection_checksum

    def to_dict(self) -> Dict[str, Any]:
        return {
            "projection_id": self.projection_id,
            "created_at": self.created_at.isoformat(),
            "view_type": self.view_type.value,
            "provider": self.provider,
            "source_trace_id": self.source_trace_id,
            "compiled_context": self.compiled_context,
            "sections": self.sections,
            "projection_checksum": self.projection_checksum,
        }


class SemanticProjectionEngine:
    """Transforms shared runtime cognition into role-specific projections."""

    def project(
        self,
        source_trace_id: str,
        compiled_context: str,
        provider: str,
        view_definition: ViewDefinition,
    ) -> SemanticProjection:
        view_type = view_definition.view_type
        projection_id = f"proj-{view_type.value}-{source_trace_id[:8]}"

        sections = self._extract_sections(compiled_context)
        shaped_sections = self._shape_sections_for_view(view_type, sections)
        projection_text = self._assemble_projection(view_type, shaped_sections)

        projection = SemanticProjection(
            projection_id=projection_id,
            created_at=datetime.now(timezone.utc),
            view_type=view_type,
            provider=provider,
            source_trace_id=source_trace_id,
            compiled_context=projection_text,
            sections=shaped_sections,
        )
        projection.calculate_checksum()
        return projection

    def compare_projections(
        self,
        projection_a: SemanticProjection,
        projection_b: SemanticProjection,
    ) -> Dict[str, Any]:
        """Compare two projections for overlap/divergence."""
        tokens_a = self._tokenize(projection_a.compiled_context)
        tokens_b = self._tokenize(projection_b.compiled_context)

        set_a = set(tokens_a)
        set_b = set(tokens_b)
        intersection = set_a.intersection(set_b)
        union = set_a.union(set_b)

        jaccard = (len(intersection) / len(union)) if union else 1.0
        divergence = 1.0 - jaccard

        section_overlap = {}
        for key in set(projection_a.sections.keys()).union(projection_b.sections.keys()):
            text_a = projection_a.sections.get(key, "")
            text_b = projection_b.sections.get(key, "")
            toks_a = set(self._tokenize(text_a))
            toks_b = set(self._tokenize(text_b))
            denom = len(toks_a.union(toks_b))
            section_overlap[key] = (len(toks_a.intersection(toks_b)) / denom) if denom else 1.0

        return {
            "projection_a": projection_a.projection_id,
            "projection_b": projection_b.projection_id,
            "jaccard_overlap": jaccard,
            "semantic_divergence": divergence,
            "shared_tokens": len(intersection),
            "projection_a_tokens": len(tokens_a),
            "projection_b_tokens": len(tokens_b),
            "section_overlap": section_overlap,
        }

    def compare_projection_set(self, projections: List[SemanticProjection]) -> Dict[str, Any]:
        """Pairwise compare a set of projections."""
        pairwise: List[Dict[str, Any]] = []
        for idx in range(len(projections)):
            for jdx in range(idx + 1, len(projections)):
                pairwise.append(self.compare_projections(projections[idx], projections[jdx]))

        avg_divergence = (
            sum(item["semantic_divergence"] for item in pairwise) / len(pairwise)
            if pairwise
            else 0.0
        )
        avg_overlap = (
            sum(item["jaccard_overlap"] for item in pairwise) / len(pairwise)
            if pairwise
            else 1.0
        )

        return {
            "projection_count": len(projections),
            "pairwise_comparisons": pairwise,
            "avg_semantic_divergence": avg_divergence,
            "avg_semantic_overlap": avg_overlap,
        }

    def _extract_sections(self, compiled_context: str) -> Dict[str, str]:
        """Extract coarse semantic sections from compiled context."""
        lines = [line.strip() for line in compiled_context.splitlines() if line.strip()]
        if not lines:
            return {"body": compiled_context}

        sections: Dict[str, List[str]] = {
            "reasoning": [],
            "facts": [],
            "actions": [],
            "anomalies": [],
            "body": [],
        }

        for line in lines:
            lower = line.lower()
            if any(token in lower for token in ["because", "therefore", "thus", "reason", "hypothesis"]):
                sections["reasoning"].append(line)
            elif any(token in lower for token in ["citation", "source", "http", "paper", "evidence", "reference"]):
                sections["facts"].append(line)
            elif any(token in lower for token in ["step", "todo", "execute", "run", "api", "tool", "command"]):
                sections["actions"].append(line)
            elif any(token in lower for token in ["conflict", "inconsisten", "gap", "missing", "contradiction"]):
                sections["anomalies"].append(line)
            sections["body"].append(line)

        return {key: "\n".join(value) for key, value in sections.items() if value}

    def _shape_sections_for_view(
        self,
        view_type: ViewType,
        sections: Dict[str, str],
    ) -> Dict[str, str]:
        """Reweight sections according to view objectives."""
        ordered_keys = {
            ViewType.RESEARCH: ["facts", "reasoning", "body", "actions", "anomalies"],
            ViewType.DRAFTER: ["reasoning", "body", "facts", "anomalies", "actions"],
            ViewType.TOOL_AGENT: ["actions", "facts", "body", "reasoning", "anomalies"],
            ViewType.CRITIC: ["anomalies", "reasoning", "facts", "body", "actions"],
        }[view_type]

        shaped: Dict[str, str] = {}
        for key in ordered_keys:
            if key in sections:
                shaped[key] = sections[key]

        # Ensure non-empty body fallback
        if "body" not in shaped:
            shaped["body"] = sections.get("body", "")

        return shaped

    def _assemble_projection(self, view_type: ViewType, sections: Dict[str, str]) -> str:
        """Assemble final projection text."""
        header = f"[VIEW:{view_type.value}]"
        blocks = [header]
        for key, value in sections.items():
            blocks.append(f"[{key.upper()}]\n{value}")
        return "\n\n".join(blocks)

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[a-zA-Z0-9_]+", text.lower())
