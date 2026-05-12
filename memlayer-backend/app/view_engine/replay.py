"""Replay and determinism support for view compilation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import hashlib
import json

from app.view_engine.compiler import ViewEngineCompiler, WorkspaceSemanticState, CompiledSemanticView
from app.view_engine.definitions import ViewType


@dataclass
class ViewReplayTrace:
    """Stored trace for deterministic view replay and historical comparisons."""

    replay_trace_id: str
    created_at: datetime
    workspace_id: str
    view_type: ViewType
    provider: str
    source_state_checksum: str
    projection_checksum: str
    runtime_trace_id: str
    quality_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "replay_trace_id": self.replay_trace_id,
            "created_at": self.created_at.isoformat(),
            "workspace_id": self.workspace_id,
            "view_type": self.view_type.value,
            "provider": self.provider,
            "source_state_checksum": self.source_state_checksum,
            "projection_checksum": self.projection_checksum,
            "runtime_trace_id": self.runtime_trace_id,
            "quality_score": self.quality_score,
            "metadata": self.metadata,
        }


class ViewReplayEngine:
    """Stores and replays view compilation traces for determinism validation."""

    def __init__(self, compiler: ViewEngineCompiler, max_traces: int = 5000):
        self.compiler = compiler
        self.max_traces = max_traces
        self.traces: List[ViewReplayTrace] = []

    def record_view(self, compiled_view: CompiledSemanticView) -> ViewReplayTrace:
        replay_trace_id = f"view-replay-{compiled_view.view_id[:16]}"
        trace = ViewReplayTrace(
            replay_trace_id=replay_trace_id,
            created_at=datetime.now(timezone.utc),
            workspace_id=compiled_view.workspace_id,
            view_type=compiled_view.view_type,
            provider=compiled_view.provider,
            source_state_checksum=compiled_view.source_state_checksum,
            projection_checksum=compiled_view.projection.projection_checksum,
            runtime_trace_id=compiled_view.runtime_trace.trace_id,
            quality_score=compiled_view.quality_report.overall_quality(),
            metadata={
                "view_quality": compiled_view.quality_report.to_dict(),
                "metrics": compiled_view.metrics.to_dict(),
            },
        )
        self.traces.append(trace)
        if len(self.traces) > self.max_traces:
            self.traces = self.traces[-self.max_traces :]
        return trace

    def replay_view(
        self,
        semantic_state: WorkspaceSemanticState,
        view_type: ViewType,
        provider: Optional[str] = None,
        token_budget: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Compile and compare replay output against historical traces."""
        compiled = self.compiler.compile_view(
            semantic_state=semantic_state,
            view_type=view_type,
            provider=provider,
            token_budget=token_budget,
        )
        new_trace = self.record_view(compiled)

        candidates = [
            trace
            for trace in self.traces
            if trace.workspace_id == semantic_state.workspace_id
            and trace.view_type == view_type
            and trace.provider == compiled.provider
            and trace.replay_trace_id != new_trace.replay_trace_id
            and trace.source_state_checksum == compiled.source_state_checksum
        ]

        previous = candidates[-1] if candidates else None
        deterministic_match = (
            previous.projection_checksum == new_trace.projection_checksum
            if previous is not None
            else True
        )

        return {
            "compiled_view": compiled.to_dict(),
            "replay_trace": new_trace.to_dict(),
            "previous_trace": previous.to_dict() if previous else None,
            "deterministic_match": deterministic_match,
        }

    def compare_replays(self, trace_id_a: str, trace_id_b: str) -> Dict[str, Any]:
        """Compare two stored replay traces."""
        a = self._get_trace(trace_id_a)
        b = self._get_trace(trace_id_b)
        if a is None or b is None:
            return {"error": "trace_not_found"}

        checksum_match = a.projection_checksum == b.projection_checksum
        quality_delta = a.quality_score - b.quality_score

        return {
            "trace_a": a.to_dict(),
            "trace_b": b.to_dict(),
            "checksum_match": checksum_match,
            "quality_delta": quality_delta,
            "is_regression": (not checksum_match) and (quality_delta < -0.01),
        }

    def get_replay_statistics(self) -> Dict[str, Any]:
        if not self.traces:
            return {"message": "no_view_replays"}

        by_view: Dict[str, int] = {}
        by_provider: Dict[str, int] = {}
        for trace in self.traces:
            by_view[trace.view_type.value] = by_view.get(trace.view_type.value, 0) + 1
            by_provider[trace.provider] = by_provider.get(trace.provider, 0) + 1

        deterministic_groups: Dict[str, List[ViewReplayTrace]] = {}
        for trace in self.traces:
            key = f"{trace.workspace_id}|{trace.view_type.value}|{trace.provider}|{trace.source_state_checksum}"
            deterministic_groups.setdefault(key, []).append(trace)

        comparisons = 0
        mismatches = 0
        for group in deterministic_groups.values():
            if len(group) < 2:
                continue
            group = sorted(group, key=lambda item: item.created_at)
            baseline = group[0].projection_checksum
            for member in group[1:]:
                comparisons += 1
                if member.projection_checksum != baseline:
                    mismatches += 1

        return {
            "total_replays": len(self.traces),
            "by_view": by_view,
            "by_provider": by_provider,
            "determinism_comparisons": comparisons,
            "determinism_mismatches": mismatches,
            "determinism_rate": (1 - mismatches / comparisons) if comparisons > 0 else 1.0,
        }

    def export_replays(self, output_file: str) -> str:
        payload = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_replays": len(self.traces),
            "statistics": self.get_replay_statistics(),
            "traces": [trace.to_dict() for trace in self.traces],
        }
        with open(output_file, "w") as file_obj:
            json.dump(payload, file_obj, indent=2)
        return output_file

    def _get_trace(self, trace_id: str) -> Optional[ViewReplayTrace]:
        for trace in self.traces:
            if trace.replay_trace_id == trace_id:
                return trace
        return None
