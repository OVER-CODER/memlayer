"""Telemetry API for Phase 8.

Exposes token analytics, latency profiling, semantic drift metrics,
provider benchmarking, and coordination diagnostics. All telemetry
is replay-compatible and exportable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json

from app.agent_runtime.runtime_kernel import SharedAgentRuntime
from app.agent_runtime.coordination_telemetry import CoordinationTelemetryService
from app.agent_runtime.coordination_policy import CoordinationPolicyEngine


class TelemetryAPI:
    """API for runtime telemetry access and analysis.

    Provides unified access to token analytics, coordination
    diagnostics, provider benchmarking, and policy traces.
    """

    def __init__(
        self,
        runtime: SharedAgentRuntime,
        policy_engine: Optional[CoordinationPolicyEngine] = None,
    ):
        self._runtime = runtime
        self._telemetry = runtime.telemetry
        self._policy = policy_engine

    # -----------------------------------------------------------------
    # Token analytics
    # -----------------------------------------------------------------

    def get_token_analytics(self) -> Dict[str, Any]:
        """Get token consumption and savings analytics."""
        reports = self._runtime._reports
        if not reports:
            return {"total_runs": 0}

        total_consumed = sum(r.total_tokens_consumed for r in reports)
        total_saved = sum(r.total_tokens_saved for r in reports)
        total_possible = total_consumed + total_saved

        per_run = [
            {
                "report_id": r.report_id,
                "tokens_consumed": r.total_tokens_consumed,
                "tokens_saved": r.total_tokens_saved,
                "savings_ratio": r.token_savings_ratio,
            }
            for r in reports[-50:]
        ]

        return {
            "total_runs": len(reports),
            "total_tokens_consumed": total_consumed,
            "total_tokens_saved": total_saved,
            "overall_savings_ratio": total_saved / max(total_possible, 1),
            "avg_tokens_per_run": total_consumed // max(len(reports), 1),
            "recent_runs": per_run,
        }

    # -----------------------------------------------------------------
    # Latency profiling
    # -----------------------------------------------------------------

    def get_latency_profile(self) -> Dict[str, Any]:
        """Get coordination latency profiling."""
        reports = self._runtime._reports
        if not reports:
            return {"total_runs": 0}

        durations = [r.coordination_duration_ms for r in reports]
        return {
            "total_runs": len(reports),
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "recent_durations": durations[-20:],
        }

    # -----------------------------------------------------------------
    # Provider benchmarking
    # -----------------------------------------------------------------

    def get_provider_benchmark(self) -> Dict[str, Any]:
        """Get provider-level performance breakdown."""
        reports = self._runtime._reports
        if not reports:
            return {"providers": {}}

        by_provider: Dict[str, Dict[str, Any]] = {}
        for r in reports:
            p = r.provider
            if p not in by_provider:
                by_provider[p] = {
                    "runs": 0, "total_tokens": 0, "total_saved": 0,
                    "durations": [], "reuse_ratios": [],
                }
            by_provider[p]["runs"] += 1
            by_provider[p]["total_tokens"] += r.total_tokens_consumed
            by_provider[p]["total_saved"] += r.total_tokens_saved
            by_provider[p]["durations"].append(r.coordination_duration_ms)
            by_provider[p]["reuse_ratios"].append(r.context_reuse_ratio)

        result = {}
        for p, data in by_provider.items():
            result[p] = {
                "runs": data["runs"],
                "total_tokens": data["total_tokens"],
                "total_saved": data["total_saved"],
                "avg_duration_ms": sum(data["durations"]) / len(data["durations"]),
                "avg_reuse_ratio": sum(data["reuse_ratios"]) / len(data["reuse_ratios"]),
                "savings_ratio": data["total_saved"] / max(data["total_tokens"] + data["total_saved"], 1),
            }

        return {"providers": result}

    # -----------------------------------------------------------------
    # Coordination diagnostics
    # -----------------------------------------------------------------

    def get_coordination_diagnostics(self) -> Dict[str, Any]:
        """Get full coordination diagnostics."""
        return self._telemetry.get_diagnostics().to_dict()

    def get_coordination_traces(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent coordination traces."""
        return [t.to_dict() for t in self._telemetry.get_recent_traces(limit)]

    # -----------------------------------------------------------------
    # Policy traces
    # -----------------------------------------------------------------

    def get_policy_traces(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get policy decision traces."""
        if self._policy:
            return self._policy.get_decision_log(limit)
        return []

    # -----------------------------------------------------------------
    # Export
    # -----------------------------------------------------------------

    def export_telemetry(self, output_file: str) -> str:
        """Export all telemetry to JSON."""
        payload = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "token_analytics": self.get_token_analytics(),
            "latency_profile": self.get_latency_profile(),
            "provider_benchmark": self.get_provider_benchmark(),
            "coordination_diagnostics": self.get_coordination_diagnostics(),
        }
        with open(output_file, "w") as f:
            json.dump(payload, f, indent=2)
        return output_file

    def get_runtime_summary(self) -> Dict[str, Any]:
        """Get a compact runtime summary."""
        return {
            "token_analytics": self.get_token_analytics(),
            "latency": self.get_latency_profile(),
            "providers": self.get_provider_benchmark(),
            "coordination": self.get_coordination_diagnostics(),
        }
