"""Replay API for Phase 8.

Provides deterministic replay of runtime executions and coordination
cycles, inspection of replay traces, and comparison of historical runs.
All replay operations are deterministic by construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.view_engine.compiler import ViewEngineCompiler, WorkspaceSemanticState
from app.view_engine.definitions import ViewType
from app.agent_runtime.runtime_kernel import SharedAgentRuntime, CoordinatedExecutionReport
from app.agent_runtime.coordination_telemetry import CoordinationTelemetryService


@dataclass
class ReplayResult:
    """Result of a replay operation."""

    replay_id: str
    original_id: str
    workspace_id: str
    is_deterministic: bool
    checksum_match: bool
    original_checksums: Dict[str, str] = field(default_factory=dict)
    replay_checksums: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "replay_id": self.replay_id,
            "original_id": self.original_id,
            "workspace_id": self.workspace_id,
            "is_deterministic": self.is_deterministic,
            "checksum_match": self.checksum_match,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ReplayComparisonResult:
    """Result of comparing two historical executions."""

    run_id_a: str
    run_id_b: str
    matching_checksums: int
    total_checksums: int
    match_ratio: float
    divergences: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id_a": self.run_id_a,
            "run_id_b": self.run_id_b,
            "matching_checksums": self.matching_checksums,
            "total_checksums": self.total_checksums,
            "match_ratio": round(self.match_ratio, 4),
            "divergences": self.divergences,
        }


class ReplayAPI:
    """API for replaying and comparing runtime executions.

    Guarantees deterministic replay: given the same WorkspaceSemanticState,
    the same projections and coordination results are produced.
    """

    def __init__(
        self,
        runtime: SharedAgentRuntime,
        telemetry: Optional[CoordinationTelemetryService] = None,
    ):
        self._runtime = runtime
        self._telemetry = telemetry or runtime.telemetry
        self._replay_history: List[ReplayResult] = []
        self._replay_counter = 0

    def replay_coordination(
        self,
        semantic_state: WorkspaceSemanticState,
        original_report: CoordinatedExecutionReport,
        provider: Optional[str] = None,
    ) -> ReplayResult:
        """Replay a coordination run and verify determinism."""
        self._replay_counter += 1
        resolved_provider = provider or original_report.provider

        # Execute fresh coordination
        replay_report = self._runtime.execute_coordinated(
            semantic_state=semantic_state,
            provider=resolved_provider,
            report_id=f"replay-{self._replay_counter:04d}",
        )

        # Compare checksums
        orig_checksums = {
            at: r.projection_checksum
            for at, r in original_report.agent_results.items()
        }
        replay_checksums = {
            at: r.projection_checksum
            for at, r in replay_report.agent_results.items()
        }
        checksum_match = orig_checksums == replay_checksums

        result = ReplayResult(
            replay_id=f"replay-{self._replay_counter:04d}",
            original_id=original_report.report_id,
            workspace_id=semantic_state.workspace_id,
            is_deterministic=checksum_match,
            checksum_match=checksum_match,
            original_checksums=orig_checksums,
            replay_checksums=replay_checksums,
        )
        self._replay_history.append(result)
        return result

    def replay_view(
        self,
        semantic_state: WorkspaceSemanticState,
        view_type: str = "research",
        provider: Optional[str] = None,
        expected_checksum: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Replay a single view compilation and verify."""
        resolved_provider = provider or semantic_state.provider
        vt = ViewType(view_type)

        compiled = self._runtime.view_compiler.compile_view(
            semantic_state, view_type=vt, provider=resolved_provider,
        )
        actual_checksum = compiled.projection.projection_checksum

        return {
            "view_type": view_type,
            "provider": resolved_provider,
            "checksum": actual_checksum,
            "checksum_match": (actual_checksum == expected_checksum) if expected_checksum else None,
            "quality": compiled.quality_report.overall_quality(),
        }

    def compare_runs(
        self,
        report_a: CoordinatedExecutionReport,
        report_b: CoordinatedExecutionReport,
    ) -> ReplayComparisonResult:
        """Compare two historical coordination reports."""
        all_agents = set(report_a.agent_results.keys()) | set(report_b.agent_results.keys())
        matching = 0
        divergences = []

        for agent in all_agents:
            r_a = report_a.agent_results.get(agent)
            r_b = report_b.agent_results.get(agent)

            if r_a and r_b:
                if r_a.projection_checksum == r_b.projection_checksum:
                    matching += 1
                else:
                    divergences.append(f"{agent}: checksum mismatch")
            else:
                divergences.append(f"{agent}: missing in one run")

        total = len(all_agents)
        return ReplayComparisonResult(
            run_id_a=report_a.report_id,
            run_id_b=report_b.report_id,
            matching_checksums=matching,
            total_checksums=total,
            match_ratio=matching / total if total > 0 else 0.0,
            divergences=divergences,
        )

    def get_replay_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get replay history."""
        return [r.to_dict() for r in self._replay_history[-limit:]]

    def get_replay_diagnostics(self) -> Dict[str, Any]:
        """Get replay diagnostics."""
        if not self._replay_history:
            return {"total_replays": 0}

        deterministic = sum(1 for r in self._replay_history if r.is_deterministic)
        return {
            "total_replays": len(self._replay_history),
            "deterministic_count": deterministic,
            "determinism_ratio": deterministic / len(self._replay_history),
            "coordination_traces": len(self._telemetry.get_recent_traces(100)),
        }
