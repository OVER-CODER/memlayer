"""
Operational Observability Layer for MemLayer.
Provides structured logging, Prometheus metrics, and runtime health monitoring.
"""

import time
import logging
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, Summary

# --- Prometheus Metrics Definitions ---

# Token Economics
TOKENS_SAVED = Counter(
    "memlayer_tokens_saved_total",
    "Total tokens saved through semantic deduplication and compression",
    ["workspace_id", "provider"]
)

COMPILATION_LATENCY = Histogram(
    "memlayer_compilation_duration_seconds",
    "Time spent in the adaptive assembly pipeline",
    ["stage", "provider"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Coordination Health
ACTIVE_COORDINATIONS = Gauge(
    "memlayer_active_coordinations",
    "Number of currently executing cognition runs"
)

REPLAY_FIDELITY = Summary(
    "memlayer_replay_fidelity_score",
    "Fidelity score of historical replays",
    ["workspace_id"]
)

# Governance & Security
GOVERNANCE_VIOLATIONS = Counter(
    "memlayer_governance_violations_total",
    "Number of runtime policy violations detected",
    ["policy_id", "severity"]
)

AUTH_FAILURES = Counter(
    "memlayer_auth_failures_total",
    "Number of authentication failures detected",
    ["tenant_id", "auth_type"]
)

RBAC_VIOLATIONS = Counter(
    "memlayer_rbac_violations_total",
    "Number of unauthorized permission attempts",
    ["tenant_id", "role", "permission"]
)


class RuntimeObservability:
    """
    Structured logging and metric emission for the MemLayer kernel.
    """

    def __init__(self, name: str = "memlayer"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

    def log_execution(self, trace_id: str, query: str, duration_ms: float, success: bool):
        """Log a structured execution summary."""
        self.logger.info(
            f"Trace: {trace_id} | Success: {success} | "
            f"Duration: {duration_ms:.2f}ms | Query: {query[:50]}..."
        )

    def record_stage_latency(self, stage: str, provider: str, duration_sec: float):
        """Record latency for a specific compilation stage."""
        COMPILATION_LATENCY.labels(stage=stage, provider=provider).observe(duration_sec)

    def record_token_savings(self, workspace_id: str, provider: str, count: int):
        """Record token savings."""
        TOKENS_SAVED.labels(workspace_id=workspace_id, provider=provider).inc(count)

    def record_replay_fidelity(self, workspace_id: str, score: float):
        """Record replay fidelity."""
        REPLAY_FIDELITY.labels(workspace_id=workspace_id).observe(score)


_observability: Optional[RuntimeObservability] = None


def get_observability() -> RuntimeObservability:
    """Get the global observability instance."""
    global _observability
    if _observability is None:
        _observability = RuntimeObservability()
    return _observability
