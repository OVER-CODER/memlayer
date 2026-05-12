"""Projection Refresh Manager for Phase 7.5.

Determines when cached projections should be refreshed, avoids
unnecessary recompilation, detects semantic staleness, and optimizes
projection reuse. All decisions are deterministic and policy-driven.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.agent_runtime.coordination_policy import (
    CoordinationPolicyEngine,
    PolicyDecision,
)


@dataclass
class ProjectionFreshnessRecord:
    """Tracks freshness state for a cached projection."""

    cache_key: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    access_count: int = 0
    refresh_count: int = 0
    semantic_drift_estimate: float = 0.0

    def age_seconds(self) -> float:
        return (datetime.now(timezone.utc) - self.created_at).total_seconds()


@dataclass
class RefreshDecision:
    """Outcome of a projection refresh evaluation."""

    cache_key: str
    action: str  # "reuse" or "refresh"
    rationale: str
    projection_age_seconds: float
    access_count: int
    policy_decision: PolicyDecision
    tokens_saved: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cache_key": self.cache_key,
            "action": self.action,
            "rationale": self.rationale,
            "projection_age_seconds": self.projection_age_seconds,
            "access_count": self.access_count,
            "tokens_saved": self.tokens_saved,
        }


class ProjectionRefreshManager:
    """Manages projection freshness and refresh decisions.

    Guarantees:
    - Stale projections are detected deterministically
    - Unnecessary recompilation is avoided
    - Refresh frequency and reuse efficiency are tracked
    - All decisions are policy-driven and replayable
    """

    def __init__(self, policy_engine: Optional[CoordinationPolicyEngine] = None):
        self.policy = policy_engine or CoordinationPolicyEngine()
        self._freshness: Dict[str, ProjectionFreshnessRecord] = {}
        self._decisions: List[RefreshDecision] = []

    def register_projection(
        self,
        cache_key: str,
        estimated_tokens: int = 0,
    ) -> ProjectionFreshnessRecord:
        """Register a newly compiled projection."""
        record = ProjectionFreshnessRecord(cache_key=cache_key)
        self._freshness[cache_key] = record
        return record

    def record_access(self, cache_key: str) -> None:
        """Record an access to a cached projection."""
        record = self._freshness.get(cache_key)
        if record:
            record.access_count += 1
            record.last_accessed_at = datetime.now(timezone.utc)

    def update_drift_estimate(self, cache_key: str, drift: float) -> None:
        """Update semantic drift estimate for a projection."""
        record = self._freshness.get(cache_key)
        if record:
            record.semantic_drift_estimate = drift

    def evaluate_refresh(
        self,
        cache_key: str,
        workspace_id: str = "",
        estimated_recompile_tokens: int = 0,
    ) -> RefreshDecision:
        """Evaluate whether a cached projection should be refreshed."""
        record = self._freshness.get(cache_key)
        if not record:
            # Unknown projection — force refresh
            policy_dec = self.policy.evaluate_projection_refresh(
                workspace_id=workspace_id,
                projection_age_seconds=0.0,
                access_count=0,
                semantic_drift_estimate=1.0,
            )
            decision = RefreshDecision(
                cache_key=cache_key,
                action="refresh",
                rationale="unknown_projection",
                projection_age_seconds=0.0,
                access_count=0,
                policy_decision=policy_dec,
            )
            self._decisions.append(decision)
            return decision

        age = record.age_seconds()
        policy_dec = self.policy.evaluate_projection_refresh(
            workspace_id=workspace_id,
            projection_age_seconds=age,
            access_count=record.access_count,
            semantic_drift_estimate=record.semantic_drift_estimate,
        )

        action = policy_dec.outcome  # "reuse" or "refresh"
        tokens_saved = estimated_recompile_tokens if action == "reuse" else 0

        if action == "refresh":
            record.refresh_count += 1
            record.created_at = datetime.now(timezone.utc)
            record.access_count = 0
            record.semantic_drift_estimate = 0.0

        decision = RefreshDecision(
            cache_key=cache_key,
            action=action,
            rationale=policy_dec.rationale,
            projection_age_seconds=age,
            access_count=record.access_count,
            policy_decision=policy_dec,
            tokens_saved=tokens_saved,
        )
        self._decisions.append(decision)
        return decision

    def get_refresh_metrics(self) -> Dict[str, Any]:
        """Get projection refresh efficiency metrics."""
        if not self._decisions:
            return {"message": "No refresh evaluations"}

        refreshes = sum(1 for d in self._decisions if d.action == "refresh")
        reuses = sum(1 for d in self._decisions if d.action == "reuse")
        tokens_saved = sum(d.tokens_saved for d in self._decisions)

        return {
            "total_evaluations": len(self._decisions),
            "refreshes": refreshes,
            "reuses": reuses,
            "reuse_ratio": reuses / len(self._decisions) if self._decisions else 0.0,
            "total_tokens_saved": tokens_saved,
            "tracked_projections": len(self._freshness),
        }
