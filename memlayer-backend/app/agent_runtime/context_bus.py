"""Shared Context Bus for Phase 7 Shared Agent Runtime.

Distributes compiled semantic views, synchronizes shared cognition state,
and tracks semantic reuse across coordinated agents.

The bus ensures agents NEVER independently rebuild context — all cognition
is accessed through shared, compiled projections.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
import hashlib
import json
import re

from app.view_engine.compiler import (
    CompiledSemanticView,
    ViewEngineCompiler,
    WorkspaceSemanticState,
)
from app.view_engine.definitions import ViewType
from app.agent_runtime.agents import AgentType, AGENT_VIEW_MAP


@dataclass
class ContextAccessRecord:
    """Record of a single context access by an agent."""

    agent_id: str
    agent_type: AgentType
    view_type: str
    projection_checksum: str
    tokens_accessed: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    was_cache_hit: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "view_type": self.view_type,
            "projection_checksum": self.projection_checksum,
            "tokens_accessed": self.tokens_accessed,
            "timestamp": self.timestamp.isoformat(),
            "was_cache_hit": self.was_cache_hit,
        }


@dataclass
class ContextReuseMetrics:
    """Metrics for context reuse across agents."""

    total_accesses: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_tokens_served: int = 0
    tokens_saved_by_reuse: int = 0
    unique_compilations: int = 0
    reuse_ratio: float = 0.0
    per_view_accesses: Dict[str, int] = field(default_factory=dict)
    per_agent_accesses: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_accesses": self.total_accesses,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_tokens_served": self.total_tokens_served,
            "tokens_saved_by_reuse": self.tokens_saved_by_reuse,
            "unique_compilations": self.unique_compilations,
            "reuse_ratio": self.reuse_ratio,
            "per_view_accesses": self.per_view_accesses,
            "per_agent_accesses": self.per_agent_accesses,
        }


class SharedContextBus:
    """Distributes compiled semantic views to coordinated agents.

    Core guarantees:
    - Views are compiled once, served many times
    - All agents consume the same semantic cognition state
    - Reuse metrics are tracked for every access
    - State is deterministic and replayable
    """

    def __init__(
        self,
        view_compiler: ViewEngineCompiler,
        max_cache_entries: int = 500,
    ):
        self.view_compiler = view_compiler
        self.max_cache_entries = max_cache_entries

        # Compiled view cache: key = (workspace_id, state_checksum, view_type, provider)
        self._cache: Dict[str, CompiledSemanticView] = {}
        self._compilation_order: List[str] = []

        # Access tracking
        self._access_log: List[ContextAccessRecord] = []
        self._compilation_token_cost: Dict[str, int] = {}

    def compile_shared_views(
        self,
        semantic_state: WorkspaceSemanticState,
        provider: Optional[str] = None,
    ) -> Dict[str, CompiledSemanticView]:
        """Compile all views for shared consumption.

        Views are cached by (workspace_id, state_checksum, provider).
        Repeated calls with the same state return cached views.
        """
        resolved_provider = provider or semantic_state.provider
        state_checksum = semantic_state.state_checksum()
        cache_prefix = f"{semantic_state.workspace_id}|{state_checksum}|{resolved_provider}"

        # Check if all views are already cached
        all_cached = True
        result: Dict[str, CompiledSemanticView] = {}
        for view_type in ViewType:
            cache_key = f"{cache_prefix}|{view_type.value}"
            if cache_key in self._cache:
                result[view_type.value] = self._cache[cache_key]
            else:
                all_cached = False

        if all_cached:
            return result

        # Compile all views (single compilation pass)
        compiled = self.view_compiler.compile_all_views(
            semantic_state=semantic_state,
            provider=resolved_provider,
        )

        # Cache each view
        for view_name, view in compiled.items():
            cache_key = f"{cache_prefix}|{view_name}"
            self._cache[cache_key] = view
            self._compilation_order.append(cache_key)
            self._compilation_token_cost[cache_key] = len(
                view.projection.compiled_context.split()
            )

        # Evict oldest if over limit
        while len(self._cache) > self.max_cache_entries:
            oldest_key = self._compilation_order.pop(0)
            self._cache.pop(oldest_key, None)
            self._compilation_token_cost.pop(oldest_key, None)

        return compiled

    def get_view_for_agent(
        self,
        agent_id: str,
        agent_type: AgentType,
        semantic_state: WorkspaceSemanticState,
        provider: Optional[str] = None,
    ) -> CompiledSemanticView:
        """Get the compiled semantic view for a specific agent.

        Compiles if necessary, returns cached view if available.
        Tracks access for reuse metrics.
        """
        resolved_provider = provider or semantic_state.provider
        state_checksum = semantic_state.state_checksum()
        view_type = AGENT_VIEW_MAP[agent_type]
        cache_key = f"{semantic_state.workspace_id}|{state_checksum}|{resolved_provider}|{view_type}"

        was_hit = cache_key in self._cache
        if not was_hit:
            self.compile_shared_views(semantic_state, provider=resolved_provider)

        view = self._cache[cache_key]
        tokens = len(view.projection.compiled_context.split())

        self._access_log.append(ContextAccessRecord(
            agent_id=agent_id,
            agent_type=agent_type,
            view_type=view_type,
            projection_checksum=view.projection.projection_checksum,
            tokens_accessed=tokens,
            was_cache_hit=was_hit,
        ))

        return view

    def get_reuse_metrics(self) -> ContextReuseMetrics:
        """Calculate context reuse metrics across all accesses."""
        if not self._access_log:
            return ContextReuseMetrics()

        total = len(self._access_log)
        hits = sum(1 for r in self._access_log if r.was_cache_hit)
        misses = total - hits
        total_tokens = sum(r.tokens_accessed for r in self._access_log)
        tokens_saved = sum(r.tokens_accessed for r in self._access_log if r.was_cache_hit)

        per_view: Dict[str, int] = {}
        per_agent: Dict[str, int] = {}
        for record in self._access_log:
            per_view[record.view_type] = per_view.get(record.view_type, 0) + 1
            per_agent[record.agent_id] = per_agent.get(record.agent_id, 0) + 1

        unique_checksums = len({r.projection_checksum for r in self._access_log})

        return ContextReuseMetrics(
            total_accesses=total,
            cache_hits=hits,
            cache_misses=misses,
            total_tokens_served=total_tokens,
            tokens_saved_by_reuse=tokens_saved,
            unique_compilations=unique_checksums,
            reuse_ratio=hits / total if total > 0 else 0.0,
            per_view_accesses=per_view,
            per_agent_accesses=per_agent,
        )

    def get_shared_state_summary(self) -> Dict[str, Any]:
        """Get summary of current shared cognition state."""
        metrics = self.get_reuse_metrics()
        return {
            "cached_views": len(self._cache),
            "total_accesses": metrics.total_accesses,
            "reuse_ratio": metrics.reuse_ratio,
            "tokens_saved_by_reuse": metrics.tokens_saved_by_reuse,
            "unique_compilations": metrics.unique_compilations,
            "access_log_size": len(self._access_log),
        }

    def invalidate(self, workspace_id: Optional[str] = None) -> int:
        """Invalidate cached views, optionally scoped to a workspace."""
        if workspace_id is None:
            count = len(self._cache)
            self._cache.clear()
            self._compilation_order.clear()
            self._compilation_token_cost.clear()
            return count

        keys_to_remove = [k for k in self._cache if k.startswith(f"{workspace_id}|")]
        for key in keys_to_remove:
            self._cache.pop(key, None)
            self._compilation_token_cost.pop(key, None)
        self._compilation_order = [k for k in self._compilation_order if k not in keys_to_remove]
        return len(keys_to_remove)

    def export_access_log(self, output_file: str) -> str:
        """Export access log to JSON."""
        payload = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_records": len(self._access_log),
            "reuse_metrics": self.get_reuse_metrics().to_dict(),
            "access_log": [r.to_dict() for r in self._access_log[-500:]],
        }
        with open(output_file, "w") as f:
            json.dump(payload, f, indent=2)
        return output_file
