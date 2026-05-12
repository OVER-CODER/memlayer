"""View API for Phase 8.

Exposes projection generation, cached view retrieval, projection
comparison, and diagnostics. All operations delegate to the existing
ViewEngineCompiler and SharedContextBus.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.view_engine.compiler import (
    CompiledSemanticView,
    ViewEngineCompiler,
    WorkspaceSemanticState,
)
from app.view_engine.definitions import ViewType
from app.agent_runtime.context_bus import SharedContextBus


@dataclass
class ViewResult:
    """Serializable view generation result."""

    view_type: str
    provider: str
    projection_checksum: str
    compiled_context: str
    quality_score: float
    token_count: int
    from_cache: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "view_type": self.view_type,
            "provider": self.provider,
            "projection_checksum": self.projection_checksum,
            "compiled_context_length": len(self.compiled_context),
            "quality_score": self.quality_score,
            "token_count": self.token_count,
            "from_cache": self.from_cache,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ViewComparisonResult:
    """Result of comparing two projections."""

    view_type: str
    provider_a: str
    provider_b: str
    checksum_a: str
    checksum_b: str
    checksums_match: bool
    quality_a: float
    quality_b: float
    quality_delta: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "view_type": self.view_type,
            "provider_a": self.provider_a,
            "provider_b": self.provider_b,
            "checksums_match": self.checksums_match,
            "quality_a": self.quality_a,
            "quality_b": self.quality_b,
            "quality_delta": round(self.quality_delta, 4),
        }


class ViewAPI:
    """API for projection generation and inspection.

    Wraps ViewEngineCompiler and SharedContextBus to provide
    a clean external interface for view operations.
    """

    def __init__(self, compiler: ViewEngineCompiler, context_bus: SharedContextBus):
        self._compiler = compiler
        self._bus = context_bus

    def generate_view(
        self,
        semantic_state: WorkspaceSemanticState,
        view_type: str = "research",
        provider: Optional[str] = None,
    ) -> ViewResult:
        """Generate a single projection for a view type."""
        resolved_provider = provider or semantic_state.provider
        vt = ViewType(view_type)

        compiled = self._compiler.compile_view(
            semantic_state, view_type=vt, provider=resolved_provider,
        )
        tokens = len(compiled.projection.compiled_context.split())

        return ViewResult(
            view_type=view_type,
            provider=resolved_provider,
            projection_checksum=compiled.projection.projection_checksum,
            compiled_context=compiled.projection.compiled_context,
            quality_score=compiled.quality_report.overall_quality(),
            token_count=tokens,
        )

    def generate_all_views(
        self,
        semantic_state: WorkspaceSemanticState,
        provider: Optional[str] = None,
    ) -> Dict[str, ViewResult]:
        """Generate all view types for a semantic state."""
        resolved_provider = provider or semantic_state.provider
        compiled = self._compiler.compile_all_views(semantic_state, provider=resolved_provider)

        results = {}
        for view_name, view in compiled.items():
            tokens = len(view.projection.compiled_context.split())
            results[view_name] = ViewResult(
                view_type=view_name,
                provider=resolved_provider,
                projection_checksum=view.projection.projection_checksum,
                compiled_context=view.projection.compiled_context,
                quality_score=view.quality_report.overall_quality(),
                token_count=tokens,
            )
        return results

    def get_cached_views(
        self,
        semantic_state: WorkspaceSemanticState,
        provider: Optional[str] = None,
    ) -> Dict[str, ViewResult]:
        """Retrieve cached views from the shared context bus."""
        resolved_provider = provider or semantic_state.provider
        compiled = self._bus.compile_shared_views(semantic_state, resolved_provider)

        results = {}
        for view_name, view in compiled.items():
            tokens = len(view.projection.compiled_context.split())
            results[view_name] = ViewResult(
                view_type=view_name,
                provider=resolved_provider,
                projection_checksum=view.projection.projection_checksum,
                compiled_context=view.projection.compiled_context,
                quality_score=view.quality_report.overall_quality(),
                token_count=tokens,
                from_cache=True,
            )
        return results

    def compare_projections(
        self,
        semantic_state: WorkspaceSemanticState,
        provider_a: str,
        provider_b: str,
        view_type: str = "research",
    ) -> ViewComparisonResult:
        """Compare projections across two providers."""
        view_a = self.generate_view(semantic_state, view_type, provider_a)
        view_b = self.generate_view(semantic_state, view_type, provider_b)

        return ViewComparisonResult(
            view_type=view_type,
            provider_a=provider_a,
            provider_b=provider_b,
            checksum_a=view_a.projection_checksum,
            checksum_b=view_b.projection_checksum,
            checksums_match=view_a.projection_checksum == view_b.projection_checksum,
            quality_a=view_a.quality_score,
            quality_b=view_b.quality_score,
            quality_delta=view_a.quality_score - view_b.quality_score,
        )

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get view API diagnostics."""
        bus_metrics = self._bus.get_reuse_metrics()
        return {
            "context_bus": self._bus.get_shared_state_summary(),
            "reuse_metrics": bus_metrics.to_dict(),
        }
