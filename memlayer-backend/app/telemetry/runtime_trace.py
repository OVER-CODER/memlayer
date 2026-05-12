"""
Runtime Trace System for Phase 5.

Provides structured tracing of the entire compiler pipeline with
complete state tracking, semantic metrics, and provider intelligence.

Traces are deterministic, reproducible, and fully persistent.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
import logging
import json
import uuid

logger = logging.getLogger(__name__)


class TraceStage(Enum):
    """Compiler pipeline stages."""

    RETRIEVAL = "retrieval"
    DEDUPLICATION = "deduplication"
    CHUNKING = "chunking"
    COMPRESSION = "compression"
    RANKING = "ranking"
    ADAPTIVE_PLANNING = "adaptive_planning"
    TOKEN_ALLOCATION = "token_allocation"
    ASSEMBLY = "assembly"
    QUALITY_CHECK = "quality_check"
    GENERATION = "generation"


class TraceLevel(Enum):
    """Trace verbosity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class SemanticMetrics:
    """Semantic quality metrics for a trace stage."""

    semantic_density: float = 0.0
    redundancy_ratio: float = 0.0
    entity_continuity: float = 0.0
    reasoning_preservation: float = 0.0
    topic_preservation: float = 0.0
    provider_compatibility: float = 0.0
    compression_effectiveness: float = 0.0

    def average_quality(self) -> float:
        """Calculate average quality across all dimensions."""
        values = [
            self.semantic_density,
            1.0 - self.redundancy_ratio,
            self.entity_continuity,
            self.reasoning_preservation,
            self.topic_preservation,
            self.provider_compatibility,
            self.compression_effectiveness,
        ]
        return sum(values) / len(values) if values else 0.0


@dataclass
class StageTrace:
    """Complete trace for a single pipeline stage."""

    stage: TraceStage
    timestamp: datetime
    duration_ms: float

    # Input/Output state
    input_token_count: int = 0
    output_token_count: int = 0
    input_items_count: int = 0
    output_items_count: int = 0

    # Compression metrics
    compression_ratio: float = 0.0
    token_savings: int = 0

    # Quality metrics
    semantic_metrics: SemanticMetrics = field(default_factory=SemanticMetrics)

    # Provider info
    provider_type: str = "generic"
    provider_metadata: Dict = field(default_factory=dict)

    # Items involved
    memory_ids_involved: List[str] = field(default_factory=list)
    item_ids_processed: List[str] = field(default_factory=list)

    # Additional context
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for persistence."""
        return {
            "stage": self.stage.value,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "input_token_count": self.input_token_count,
            "output_token_count": self.output_token_count,
            "input_items_count": self.input_items_count,
            "output_items_count": self.output_items_count,
            "compression_ratio": self.compression_ratio,
            "token_savings": self.token_savings,
            "semantic_metrics": asdict(self.semantic_metrics),
            "provider_type": self.provider_type,
            "provider_metadata": self.provider_metadata,
            "memory_ids_involved": self.memory_ids_involved,
            "item_ids_processed": self.item_ids_processed,
            "notes": self.notes,
            "metadata": self.metadata,
        }


@dataclass
class ExecutionTrace:
    """Complete trace of a full compiler execution."""

    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    query_type: str = "unknown"
    provider: str = "generic"
    compression_mode: str = "balanced"
    token_budget: int = 4000

    # Timeline
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    total_duration_ms: float = 0.0

    # Stages
    stages: List[StageTrace] = field(default_factory=list)

    # Overall metrics
    input_memories_count: int = 0
    output_context_tokens: int = 0
    total_token_savings: int = 0

    # Quality
    overall_quality_score: float = 0.0
    semantic_retention: float = 0.0

    # Status
    success: bool = True
    error_message: Optional[str] = None

    # Analytics
    stage_breakdown: Dict[str, float] = field(
        default_factory=dict
    )  # stage -> percentage of total time

    def add_stage(self, stage_trace: StageTrace) -> None:
        """Add a stage trace."""
        self.stages.append(stage_trace)

    def finalize(self) -> None:
        """Finalize trace after execution."""
        self.completed_at = datetime.now(timezone.utc)
        self.total_duration_ms = (
            self.completed_at - self.started_at
        ).total_seconds() * 1000

        # Calculate stage breakdown
        if self.total_duration_ms > 0:
            for stage in self.stages:
                stage_name = stage.stage.value
                percentage = (stage.duration_ms / self.total_duration_ms) * 100
                self.stage_breakdown[stage_name] = percentage

    def to_dict(self) -> Dict:
        """Convert to dictionary for persistence."""
        return {
            "trace_id": self.trace_id,
            "query": self.query,
            "query_type": self.query_type,
            "provider": self.provider,
            "compression_mode": self.compression_mode,
            "token_budget": self.token_budget,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "total_duration_ms": self.total_duration_ms,
            "stages": [s.to_dict() for s in self.stages],
            "input_memories_count": self.input_memories_count,
            "output_context_tokens": self.output_context_tokens,
            "total_token_savings": self.total_token_savings,
            "overall_quality_score": self.overall_quality_score,
            "semantic_retention": self.semantic_retention,
            "success": self.success,
            "error_message": self.error_message,
            "stage_breakdown": self.stage_breakdown,
        }


class RuntimeTraceService:
    """
    Complete runtime tracing for the compiler pipeline.

    Emits structured traces for every stage with complete state tracking,
    semantic metrics, and provider intelligence.
    """

    def __init__(self, max_history: int = 10000):
        """
        Initialize trace service.

        Args:
            max_history: Maximum number of traces to keep in memory
        """
        self.max_history = max_history
        self.traces: List[ExecutionTrace] = []
        self.current_trace: Optional[ExecutionTrace] = None

    def start_execution(
        self,
        query: str,
        query_type: str = "unknown",
        provider: str = "generic",
        compression_mode: str = "balanced",
        token_budget: int = 4000,
        input_memories_count: int = 0,
    ) -> ExecutionTrace:
        """Start a new execution trace."""
        trace = ExecutionTrace(
            query=query,
            query_type=query_type,
            provider=provider,
            compression_mode=compression_mode,
            token_budget=token_budget,
            input_memories_count=input_memories_count,
        )
        self.current_trace = trace
        logger.debug(f"Started trace {trace.trace_id} for query: {query[:50]}")
        return trace

    def record_stage(
        self,
        stage: TraceStage,
        duration_ms: float,
        input_token_count: int = 0,
        output_token_count: int = 0,
        input_items_count: int = 0,
        output_items_count: int = 0,
        compression_ratio: float = 0.0,
        semantic_metrics: Optional[SemanticMetrics] = None,
        provider_type: str = "generic",
        memory_ids_involved: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        notes: str = "",
    ) -> None:
        """Record a pipeline stage."""
        if self.current_trace is None:
            logger.warning("No active trace, starting default trace")
            self.start_execution("unknown")

        stage_trace = StageTrace(
            stage=stage,
            timestamp=datetime.now(timezone.utc),
            duration_ms=duration_ms,
            input_token_count=input_token_count,
            output_token_count=output_token_count,
            input_items_count=input_items_count,
            output_items_count=output_items_count,
            compression_ratio=compression_ratio,
            token_savings=max(0, input_token_count - output_token_count),
            semantic_metrics=semantic_metrics or SemanticMetrics(),
            provider_type=provider_type,
            memory_ids_involved=memory_ids_involved or [],
            metadata=metadata or {},
            notes=notes,
        )

        self.current_trace.add_stage(stage_trace)
        logger.debug(
            f"Recorded stage {stage.value}: {duration_ms:.2f}ms, "
            f"tokens: {input_token_count} -> {output_token_count}"
        )

    def finalize_execution(
        self,
        success: bool = True,
        error_message: Optional[str] = None,
        output_context_tokens: int = 0,
        overall_quality_score: float = 0.0,
        semantic_retention: float = 0.0,
    ) -> ExecutionTrace:
        """Finalize the current execution trace."""
        if self.current_trace is None:
            logger.warning("No active trace to finalize")
            return ExecutionTrace()

        self.current_trace.success = success
        self.current_trace.error_message = error_message
        self.current_trace.output_context_tokens = output_context_tokens
        self.current_trace.overall_quality_score = overall_quality_score
        self.current_trace.semantic_retention = semantic_retention
        self.current_trace.total_token_savings = sum(
            s.token_savings for s in self.current_trace.stages
        )

        self.current_trace.finalize()

        # Store trace
        self.traces.append(self.current_trace)

        # Trim history
        if len(self.traces) > self.max_history:
            self.traces = self.traces[-self.max_history :]

        trace_id = self.current_trace.trace_id
        logger.debug(
            f"Finalized trace {trace_id}: "
            f"success={success}, quality={overall_quality_score:.3f}, "
            f"duration={self.current_trace.total_duration_ms:.2f}ms"
        )

        result = self.current_trace
        self.current_trace = None
        return result

    def get_trace(self, trace_id: str) -> Optional[ExecutionTrace]:
        """Get a specific trace by ID."""
        for trace in self.traces:
            if trace.trace_id == trace_id:
                return trace
        return None

    def get_recent_traces(self, limit: int = 100) -> List[ExecutionTrace]:
        """Get recent execution traces."""
        return self.traces[-limit:]

    def get_trace_statistics(self) -> Dict:
        """Get statistics about all traces."""
        if not self.traces:
            return {"message": "No traces recorded"}

        total_traces = len(self.traces)
        successful_traces = sum(1 for t in self.traces if t.success)
        failed_traces = total_traces - successful_traces

        total_duration = sum(t.total_duration_ms for t in self.traces)
        avg_duration = total_duration / total_traces if total_traces > 0 else 0

        total_savings = sum(t.total_token_savings for t in self.traces)
        avg_quality = (
            sum(t.overall_quality_score for t in self.traces) / total_traces
            if total_traces > 0
            else 0
        )

        # Stage statistics
        stage_stats = {}
        for trace in self.traces:
            for stage in trace.stages:
                stage_name = stage.stage.value
                if stage_name not in stage_stats:
                    stage_stats[stage_name] = {
                        "count": 0,
                        "total_duration_ms": 0.0,
                    }
                stage_stats[stage_name]["count"] += 1
                stage_stats[stage_name]["total_duration_ms"] += stage.duration_ms

        # Calculate averages for stages
        for stage_name in stage_stats:
            count = stage_stats[stage_name]["count"]
            if count > 0:
                stage_stats[stage_name]["avg_duration_ms"] = (
                    stage_stats[stage_name]["total_duration_ms"] / count
                )

        return {
            "total_traces": total_traces,
            "successful_traces": successful_traces,
            "failed_traces": failed_traces,
            "success_rate": successful_traces / total_traces
            if total_traces > 0
            else 0.0,
            "total_duration_ms": total_duration,
            "avg_duration_ms": avg_duration,
            "total_token_savings": total_savings,
            "avg_quality_score": avg_quality,
            "stage_statistics": stage_stats,
        }

    def export_traces(self, output_file: str) -> str:
        """Export all traces to JSON file."""
        traces_data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_traces": len(self.traces),
            "traces": [t.to_dict() for t in self.traces],
        }

        with open(output_file, "w") as f:
            json.dump(traces_data, f, indent=2)

        logger.info(f"Exported {len(self.traces)} traces to {output_file}")
        return output_file


# Global trace service instance
_trace_service: Optional[RuntimeTraceService] = None


def get_trace_service() -> RuntimeTraceService:
    """Get or create the global trace service."""
    global _trace_service
    if _trace_service is None:
        _trace_service = RuntimeTraceService()
    return _trace_service
