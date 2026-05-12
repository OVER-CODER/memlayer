"""View Engine Compiler core for Phase 6 cognition virtualization."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import hashlib
import json

from app.runtime.integrated_runtime import IntegratedRuntimeSystem, UnifiedCognitionTrace
from app.view_engine.definitions import ViewDefinitionFramework, ViewDefinition, ViewType
from app.view_engine.projection import SemanticProjectionEngine, SemanticProjection
from app.view_engine.quality import ViewQualityEvaluator, ViewQualityReport


@dataclass
class WorkspaceSemanticState:
    """Input workspace semantic state for view compilation."""

    workspace_id: str
    query: str
    memories: List[Any]
    provider: str = "claude"
    token_budget: int = 4000
    query_type: str = "general"
    original_context: str = ""
    workspace_state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def state_checksum(self) -> str:
        raw = {
            "workspace_id": self.workspace_id,
            "query": self.query,
            "provider": self.provider,
            "token_budget": self.token_budget,
            "query_type": self.query_type,
            "memory_ids": [getattr(memory, "id", str(idx)) for idx, memory in enumerate(self.memories)],
            "metadata": self.metadata,
        }
        return hashlib.sha256(json.dumps(raw, sort_keys=True, default=str).encode()).hexdigest()[:24]


@dataclass
class ViewCompilationMetrics:
    """Metrics for a compiled view."""

    view_id: str
    view_type: ViewType
    provider: str
    token_budget_used: int
    selected_memory_count: int
    selection_ratio: float
    runtime_trace_id: str
    projection_checksum: str
    semantic_divergence_from_base: float
    compiled_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "view_id": self.view_id,
            "view_type": self.view_type.value,
            "provider": self.provider,
            "token_budget_used": self.token_budget_used,
            "selected_memory_count": self.selected_memory_count,
            "selection_ratio": self.selection_ratio,
            "runtime_trace_id": self.runtime_trace_id,
            "projection_checksum": self.projection_checksum,
            "semantic_divergence_from_base": self.semantic_divergence_from_base,
            "compiled_at": self.compiled_at.isoformat(),
        }


@dataclass
class CompiledSemanticView:
    """Compiled role-specific semantic view output."""

    view_id: str
    workspace_id: str
    view_type: ViewType
    provider: str
    source_state_checksum: str
    runtime_trace: UnifiedCognitionTrace
    projection: SemanticProjection
    quality_report: ViewQualityReport
    metrics: ViewCompilationMetrics

    def to_dict(self) -> Dict[str, Any]:
        return {
            "view_id": self.view_id,
            "workspace_id": self.workspace_id,
            "view_type": self.view_type.value,
            "provider": self.provider,
            "source_state_checksum": self.source_state_checksum,
            "runtime_trace": self.runtime_trace.to_dict(),
            "projection": self.projection.to_dict(),
            "quality_report": self.quality_report.to_dict(),
            "metrics": self.metrics.to_dict(),
        }


class ViewEngineCompiler:
    """
    Compiles role-optimized semantic projections from shared cognition state.

    Integrates with adaptive runtime/telemetry and produces deterministic,
    replay-compatible specialized views.
    """

    def __init__(
        self,
        runtime_system: IntegratedRuntimeSystem,
        definition_framework: Optional[ViewDefinitionFramework] = None,
        projection_engine: Optional[SemanticProjectionEngine] = None,
        quality_evaluator: Optional[ViewQualityEvaluator] = None,
    ):
        self.runtime = runtime_system
        self.definition_framework = definition_framework or ViewDefinitionFramework()
        self.projection_engine = projection_engine or SemanticProjectionEngine()
        self.quality_evaluator = quality_evaluator or ViewQualityEvaluator()
        self.compiled_views: List[CompiledSemanticView] = []

    def compile_view(
        self,
        semantic_state: WorkspaceSemanticState,
        view_type: ViewType,
        provider: Optional[str] = None,
        token_budget: Optional[int] = None,
    ) -> CompiledSemanticView:
        """Compile a single role-specific semantic view."""
        definition = self.definition_framework.get_view_definition(view_type)
        resolved_provider = provider or semantic_state.provider

        selected_memories = self._select_memories(semantic_state.memories, definition)
        resolved_budget = self._resolve_token_budget(
            semantic_state.token_budget,
            token_budget,
            definition,
            resolved_provider,
        )

        shaped_query = self._shape_query(
            semantic_state.query,
            definition,
            resolved_provider,
        )

        runtime_trace = self.runtime.execute_with_telemetry(
            query=shaped_query,
            memories=selected_memories,
            original_context=semantic_state.original_context,
            token_budget=resolved_budget,
            provider=resolved_provider,
            compression_mode=definition.compression_preference,
            workspace_state=semantic_state.workspace_state,
            query_type=semantic_state.query_type,
        )

        base_compiled = (
            runtime_trace.assembly_result.compiled_context
            if runtime_trace.assembly_result
            else ""
        )
        projection = self.projection_engine.project(
            source_trace_id=runtime_trace.trace_id,
            compiled_context=base_compiled,
            provider=resolved_provider,
            view_definition=definition,
        )

        quality_report = self.quality_evaluator.evaluate(
            projection=projection,
            base_context=base_compiled,
            view_definition=definition,
            compiled_token_budget=resolved_budget,
        )

        divergence = 1.0 - quality_report.semantic_overlap_with_base
        view_id = f"view-{view_type.value}-{runtime_trace.trace_id[:8]}"
        metrics = ViewCompilationMetrics(
            view_id=view_id,
            view_type=view_type,
            provider=resolved_provider,
            token_budget_used=resolved_budget,
            selected_memory_count=len(selected_memories),
            selection_ratio=(len(selected_memories) / max(len(semantic_state.memories), 1)),
            runtime_trace_id=runtime_trace.trace_id,
            projection_checksum=projection.projection_checksum,
            semantic_divergence_from_base=divergence,
        )

        compiled = CompiledSemanticView(
            view_id=view_id,
            workspace_id=semantic_state.workspace_id,
            view_type=view_type,
            provider=resolved_provider,
            source_state_checksum=semantic_state.state_checksum(),
            runtime_trace=runtime_trace,
            projection=projection,
            quality_report=quality_report,
            metrics=metrics,
        )
        self.compiled_views.append(compiled)
        return compiled

    def compile_all_views(
        self,
        semantic_state: WorkspaceSemanticState,
        provider: Optional[str] = None,
        token_budget: Optional[int] = None,
    ) -> Dict[str, CompiledSemanticView]:
        """Compile all foundational views from same shared cognition state."""
        result: Dict[str, CompiledSemanticView] = {}
        for view_type in [ViewType.RESEARCH, ViewType.DRAFTER, ViewType.TOOL_AGENT, ViewType.CRITIC]:
            compiled = self.compile_view(
                semantic_state=semantic_state,
                view_type=view_type,
                provider=provider,
                token_budget=token_budget,
            )
            result[view_type.value] = compiled
        return result

    def compare_compiled_views(self, views: List[CompiledSemanticView]) -> Dict[str, Any]:
        """Run cross-view comparison diagnostics."""
        projections = [view.projection for view in views]
        projection_report = self.projection_engine.compare_projection_set(projections)

        quality = {}
        for view in views:
            quality[view.view_type.value] = view.quality_report.to_dict()

        return {
            "projection_report": projection_report,
            "quality_report": quality,
            "views": [view.metrics.to_dict() for view in views],
        }

    def get_view_history(
        self,
        view_type: Optional[ViewType] = None,
        provider: Optional[str] = None,
        limit: int = 100,
    ) -> List[CompiledSemanticView]:
        """Retrieve compiled view history with filtering."""
        views = self.compiled_views
        if view_type is not None:
            views = [view for view in views if view.view_type == view_type]
        if provider is not None:
            views = [view for view in views if view.provider == provider]
        return views[-limit:]

    def export_view_history(self, output_file: str) -> str:
        """Export view compilation history to JSON."""
        payload = {
            "exported_at": datetime.utcnow().isoformat(),
            "total_views": len(self.compiled_views),
            "views": [view.to_dict() for view in self.compiled_views],
        }
        with open(output_file, "w") as file_obj:
            json.dump(payload, file_obj, indent=2)
        return output_file

    def _shape_query(
        self,
        query: str,
        definition: ViewDefinition,
        provider: str,
    ) -> str:
        """Shape query with deterministic view objective prefix."""
        profile = definition.resolve_provider_profile(provider)
        objective = definition.semantic_objectives
        prefix = (
            f"[view={definition.view_type.value}] "
            f"[provider={provider}] "
            f"[breadth={objective.semantic_breadth:.2f}] "
            f"[narrative={objective.narrative_continuity:.2f}] "
            f"[actionability={objective.actionability:.2f}] "
            f"[contradiction={objective.contradiction_focus * profile.contradiction_bias:.2f}]"
        )
        return f"{prefix} {query}"

    def _resolve_token_budget(
        self,
        base_token_budget: int,
        override_token_budget: Optional[int],
        definition: ViewDefinition,
        provider: str,
    ) -> int:
        """Resolve provider/view adjusted token budget."""
        if override_token_budget is not None:
            base = override_token_budget
        else:
            base = base_token_budget
        profile = definition.resolve_provider_profile(provider)
        adjusted = int(base * definition.base_token_budget_ratio * profile.quality_bias / max(profile.compression_bias, 0.1))
        return max(256, adjusted)

    def _select_memories(self, memories: List[Any], definition: ViewDefinition) -> List[Any]:
        """Select and rank memories for a specific view using deterministic scoring."""
        if not memories:
            return []

        objective = definition.semantic_objectives
        scored: List[tuple[float, Any]] = []
        for idx, memory in enumerate(memories):
            content = str(getattr(memory, "raw_content", str(memory)))
            importance = float(getattr(memory, "importance_score", 0.5))
            length_score = min(1.0, len(content.split()) / 120.0)
            citation_score = self._contains_any(content, ["source", "http", "citation", "reference", "evidence"])
            action_score = self._contains_any(content, ["step", "run", "execute", "tool", "api", "command"])
            contradiction_score = self._contains_any(content, ["conflict", "gap", "contradiction", "inconsistent", "missing"])
            narrative_score = self._contains_any(content, ["then", "after", "before", "story", "sequence", "flow"])

            score = (
                importance * 0.30
                + length_score * objective.semantic_breadth * 0.20
                + citation_score * objective.citation_traceability * 0.15
                + action_score * objective.actionability * 0.15
                + contradiction_score * objective.contradiction_focus * 0.10
                + narrative_score * objective.narrative_continuity * 0.10
                + (1.0 / (idx + 1)) * objective.determinism_bias * 0.05
            )
            scored.append((score, memory))

        scored.sort(key=lambda item: item[0], reverse=True)
        select_count = max(1, int(len(memories) * definition.memory_selection_ratio))
        return [memory for _, memory in scored[:select_count]]

    def _contains_any(self, content: str, tokens: List[str]) -> float:
        lower = content.lower()
        hits = sum(1 for token in tokens if token in lower)
        return min(1.0, hits / max(len(tokens), 1))
