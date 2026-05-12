"""Diagnostics tooling for view engine projections and comparison."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List
import json

from app.view_engine.compiler import ViewEngineCompiler, CompiledSemanticView
from app.view_engine.replay import ViewReplayEngine


@dataclass
class ViewDiagnosticsSnapshot:
    snapshot_id: str
    generated_at: datetime
    view_counts: Dict[str, int]
    provider_distribution: Dict[str, int]
    quality_summary: Dict[str, Any]
    projection_comparison: Dict[str, Any]
    replay_summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "generated_at": self.generated_at.isoformat(),
            "view_counts": self.view_counts,
            "provider_distribution": self.provider_distribution,
            "quality_summary": self.quality_summary,
            "projection_comparison": self.projection_comparison,
            "replay_summary": self.replay_summary,
        }


class ViewDiagnosticsDashboard:
    """Developer diagnostics dashboard for view-engine outputs."""

    def __init__(self, compiler: ViewEngineCompiler, replay_engine: ViewReplayEngine):
        self.compiler = compiler
        self.replay_engine = replay_engine
        self.snapshots: List[ViewDiagnosticsSnapshot] = []

    def capture_snapshot(self, snapshot_id: str = "view-diagnostics") -> ViewDiagnosticsSnapshot:
        history = self.compiler.get_view_history(limit=1000)
        by_view: Dict[str, int] = {}
        by_provider: Dict[str, int] = {}
        quality_values: List[float] = []

        for view in history:
            by_view[view.view_type.value] = by_view.get(view.view_type.value, 0) + 1
            by_provider[view.provider] = by_provider.get(view.provider, 0) + 1
            quality_values.append(view.quality_report.overall_quality())

        quality_summary = {
            "count": len(quality_values),
            "avg_quality": (sum(quality_values) / len(quality_values)) if quality_values else 0.0,
            "min_quality": min(quality_values) if quality_values else 0.0,
            "max_quality": max(quality_values) if quality_values else 0.0,
        }

        latest_by_view: Dict[str, CompiledSemanticView] = {}
        for view in history:
            latest_by_view[view.view_type.value] = view

        comparison = self.compiler.compare_compiled_views(list(latest_by_view.values())) if latest_by_view else {}

        snapshot = ViewDiagnosticsSnapshot(
            snapshot_id=snapshot_id,
            generated_at=datetime.now(timezone.utc),
            view_counts=by_view,
            provider_distribution=by_provider,
            quality_summary=quality_summary,
            projection_comparison=comparison,
            replay_summary=self.replay_engine.get_replay_statistics(),
        )
        self.snapshots.append(snapshot)
        return snapshot

    def export_snapshot(self, snapshot: ViewDiagnosticsSnapshot, output_file: str) -> str:
        with open(output_file, "w") as file_obj:
            json.dump(snapshot.to_dict(), file_obj, indent=2)
        return output_file

    def render_console_report(self, snapshot: ViewDiagnosticsSnapshot) -> str:
        lines = [
            "=" * 80,
            "VIEW ENGINE DIAGNOSTICS",
            "=" * 80,
            f"Snapshot: {snapshot.snapshot_id}",
            f"Generated: {snapshot.generated_at.isoformat()}",
            "",
            f"Views compiled: {sum(snapshot.view_counts.values())}",
            f"View distribution: {snapshot.view_counts}",
            f"Provider distribution: {snapshot.provider_distribution}",
            "",
            f"Quality summary: {snapshot.quality_summary}",
            "",
            f"Replay summary: {snapshot.replay_summary}",
            "=" * 80,
        ]
        return "\n".join(lines)
