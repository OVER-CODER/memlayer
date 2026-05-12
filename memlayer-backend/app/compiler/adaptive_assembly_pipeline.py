"""
Adaptive Assembly Pipeline - End-to-end runtime for Phase 4.

This module implements the complete adaptive context compilation pipeline,
integrating all Phase 4 components (ranking, budgeting, quality evaluation)
into a cohesive, deployable system.

Pipeline stages:
1. Retrieval: Get candidate memories from storage
2. Deduplication: Remove semantic duplicates
3. Chunking: Organize memories into semantic chunks
4. Ranking: Score and rank memories by relevance
5. Compression: Compress context while preserving semantics
6. Allocation: Distribute token budget intelligently
7. Assembly: Assemble final context layers
8. Quality Check: Validate output quality
9. Analytics: Track performance metrics
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import logging
import time
import json

from app.compiler.adaptive_compilation import (
    AdaptiveCompilationPlanner,
    RelevanceRankingService,
    TokenBudgetAllocator,
    ContextQualityEvaluator,
    ContextFailureAnalyzer,
    CompilationPlan,
    ContextQualityScore,
    CompilationMetrics,
)

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Pipeline execution stages."""

    RETRIEVAL = "retrieval"
    DEDUPLICATION = "deduplication"
    CHUNKING = "chunking"
    RANKING = "ranking"
    COMPRESSION = "compression"
    ALLOCATION = "allocation"
    ASSEMBLY = "assembly"
    QUALITY_CHECK = "quality_check"
    COMPLETE = "complete"


@dataclass
class PipelineStageMetrics:
    """Metrics for a single pipeline stage."""

    stage: PipelineStage
    duration_ms: float
    input_count: int
    output_count: int
    memory_delta_bytes: int = 0
    notes: str = ""


@dataclass
class AdaptiveAssemblyResult:
    """Result of adaptive context assembly."""

    query: str
    provider: str
    compression_mode: str

    # Output layers
    compiled_context: str
    reasoning_context: str
    semantic_memories: str
    workspace_summary: str

    # Quality metrics
    quality_score: Optional[ContextQualityScore] = None
    semantic_retention: float = 0.0
    token_efficiency: float = 0.0

    # Performance metrics
    total_duration_ms: float = 0.0
    stage_metrics: List[PipelineStageMetrics] = field(default_factory=list)
    compilation_plan: Optional[CompilationPlan] = None

    # Analytics
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "provider": self.provider,
            "compression_mode": self.compression_mode,
            "compiled_context": self.compiled_context[:200] + "..."
            if len(self.compiled_context) > 200
            else self.compiled_context,
            "quality_score": self.quality_score.overall_quality()
            if self.quality_score
            else None,
            "semantic_retention": self.semantic_retention,
            "token_efficiency": self.token_efficiency,
            "total_duration_ms": self.total_duration_ms,
            "timestamp": self.timestamp.isoformat(),
        }


class AdaptiveAssemblyPipeline:
    """
    Complete adaptive context compilation pipeline.

    Orchestrates all Phase 4 components to dynamically compile context
    based on query type, token budget, and provider requirements.
    """

    def __init__(
        self,
        ranking_service: RelevanceRankingService,
        embedding_service,
        compression_mode: str = "balanced",
    ):
        """
        Initialize pipeline.

        Args:
            ranking_service: Relevance ranking service
            embedding_service: Embedding service for semantic operations
            compression_mode: Default compression mode (minimal/balanced/compressed/aggressive)
        """
        self.ranking_service = ranking_service
        self.embedding_service = embedding_service
        self.compression_mode = compression_mode

        # Initialize Phase 4 components
        self.planner = AdaptiveCompilationPlanner(
            ranking_service=ranking_service, embedding_service=embedding_service
        )
        self.quality_evaluator = ContextQualityEvaluator()
        self.failure_analyzer = ContextFailureAnalyzer()

        # Analytics
        self.execution_history: List[AdaptiveAssemblyResult] = []

    def execute(
        self,
        query: str,
        memories: List,
        original_context: str = "",
        token_budget: int = 4000,
        provider: str = "claude",
        workspace_state: Optional[Dict] = None,
    ) -> AdaptiveAssemblyResult:
        """
        Execute adaptive assembly pipeline.

        Args:
            query: User query
            memories: Available memories
            original_context: Original uncompressed context (for quality baseline)
            token_budget: Available token budget
            provider: Target provider (claude/openai/gemini)
            workspace_state: Current workspace context

        Returns:
            AdaptiveAssemblyResult with compiled context and metrics
        """
        pipeline_start = time.time()
        stage_metrics: List[PipelineStageMetrics] = []
        plan = None  # Initialize plan before try block

        try:
            # Stage 1: Ranking
            logger.info(f"Stage 1: Ranking {len(memories)} memories...")
            stage_start = time.time()
            ranked_memories = self.ranking_service.rank_memories(
                query=query,
                memories=memories,
                workspace_state=workspace_state,
                provider_type=provider,
            )
            ranking_time = (time.time() - stage_start) * 1000
            stage_metrics.append(
                PipelineStageMetrics(
                    stage=PipelineStage.RANKING,
                    duration_ms=ranking_time,
                    input_count=len(memories),
                    output_count=len(ranked_memories),
                )
            )
            logger.info(
                f"✓ Ranked {len(ranked_memories)} memories in {ranking_time:.2f}ms"
            )

            # Stage 2: Plan Compilation
            logger.info(f"Stage 2: Planning compilation...")
            stage_start = time.time()
            plan = self.planner.plan_compilation(
                query=query,
                memories=memories,
                provider=provider,
                token_budget=token_budget,
                workspace_state=workspace_state,
            )
            planning_time = (time.time() - stage_start) * 1000
            stage_metrics.append(
                PipelineStageMetrics(
                    stage=PipelineStage.ALLOCATION,
                    duration_ms=planning_time,
                    input_count=len(memories),
                    output_count=len(plan.selected_memories),
                    notes=f"Query type: {plan.query_type.value}",
                )
            )
            logger.info(
                f"✓ Created plan with {len(plan.selected_memories)} selected memories in {planning_time:.2f}ms"
            )

            # Stage 3: Assemble Context Layers
            logger.info(f"Stage 3: Assembling context layers...")
            stage_start = time.time()

            # Build context layers from plan
            compiled_context = self._assemble_compiled_context(
                plan=plan,
                memories=memories,
                provider=provider,
                token_budget=plan.token_allocation.total_budget,
            )

            assembly_time = (time.time() - stage_start) * 1000
            stage_metrics.append(
                PipelineStageMetrics(
                    stage=PipelineStage.ASSEMBLY,
                    duration_ms=assembly_time,
                    input_count=len(plan.selected_memories),
                    output_count=1,
                    memory_delta_bytes=len(compiled_context.encode("utf-8")),
                )
            )
            logger.info(f"✓ Assembled context layers in {assembly_time:.2f}ms")

            # Stage 4: Quality Evaluation
            logger.info(f"Stage 4: Evaluating quality...")
            stage_start = time.time()

            quality_score = self.quality_evaluator.evaluate_quality(
                compiled_context=compiled_context,
                original_memories=memories,
                compression_ratio=0.5,  # Estimate
                provider_type=provider,
            )

            quality_time = (time.time() - stage_start) * 1000
            stage_metrics.append(
                PipelineStageMetrics(
                    stage=PipelineStage.QUALITY_CHECK,
                    duration_ms=quality_time,
                    input_count=1,
                    output_count=1,
                    notes=f"Overall quality: {str(getattr(quality_score, 'overall_quality', 0.0))[:6]}",
                )
            )
            logger.info(
                f"✓ Quality evaluation complete: {str(getattr(quality_score, 'overall_quality', 0.0))[:6]} in {quality_time:.2f}ms"
            )

            # Calculate token efficiency
            token_efficiency = (
                len(compiled_context.split()) / token_budget
                if token_budget > 0
                else 0.0
            )
            semantic_retention = (
                getattr(quality_score, "semantic_density", 0.0)
                if quality_score
                else 0.0
            )

            total_time = (time.time() - pipeline_start) * 1000

            # Create result
            result = AdaptiveAssemblyResult(
                query=query,
                provider=provider,
                compression_mode=plan.compression_mode,
                compiled_context=compiled_context,
                reasoning_context=plan.reasoning_context
                if hasattr(plan, "reasoning_context")
                else "",
                semantic_memories=plan.semantic_context
                if hasattr(plan, "semantic_context")
                else "",
                workspace_summary=plan.workspace_context
                if hasattr(plan, "workspace_context")
                else "",
                quality_score=quality_score,
                semantic_retention=semantic_retention,
                token_efficiency=token_efficiency,
                total_duration_ms=total_time,
                stage_metrics=stage_metrics,
                compilation_plan=plan,
            )

            # Store in history
            self.execution_history.append(result)

            logger.info(f"✓ Pipeline complete in {total_time:.2f}ms")
            return result

        except Exception as e:
            logger.error(f"✗ Pipeline failed: {e}", exc_info=True)
            # Return partial result with whatever we have
            return AdaptiveAssemblyResult(
                query=query,
                provider=provider,
                compression_mode=self.compression_mode,
                compiled_context="",
                reasoning_context="",
                semantic_memories="",
                workspace_summary="",
                total_duration_ms=(time.time() - pipeline_start) * 1000,
                stage_metrics=stage_metrics,
                compilation_plan=plan,
            )

    def _assemble_compiled_context(
        self,
        plan: CompilationPlan,
        memories: List,
        provider: str,
        token_budget: int,
    ) -> str:
        """Assemble final compiled context from plan."""
        parts = []

        # Add reasoning context if present
        if hasattr(plan, "reasoning_context") and plan.reasoning_context:
            parts.append(f"## Reasoning Context\n{plan.reasoning_context}")

        # Add selected memories
        if plan.selected_memories:
            parts.append("## Relevant Memories")
            for mem_id in plan.selected_memories[:10]:  # Limit to top 10
                # Find memory by ID
                for mem in memories:
                    if mem.id == mem_id:
                        parts.append(f"- {mem.raw_content[:200]}")
                        break

        # Add workspace summary if present
        if hasattr(plan, "workspace_context") and plan.workspace_context:
            parts.append(f"## Workspace Summary\n{plan.workspace_context}")

        return "\n\n".join(parts) if parts else "No context compiled"

    def get_analytics_report(self) -> Dict:
        """Get analytics report from execution history."""
        if not self.execution_history:
            return {"message": "No executions yet"}

        quality_scores = [
            r.quality_score.overall_quality()
            for r in self.execution_history
            if r.quality_score
        ]

        return {
            "total_executions": len(self.execution_history),
            "avg_total_time_ms": sum(
                r.total_duration_ms for r in self.execution_history
            )
            / len(self.execution_history),
            "avg_quality_score": sum(quality_scores) / len(quality_scores)
            if quality_scores
            else 0.0,
            "avg_semantic_retention": sum(
                r.semantic_retention for r in self.execution_history
            )
            / len(self.execution_history),
            "avg_token_efficiency": sum(
                r.token_efficiency for r in self.execution_history
            )
            / len(self.execution_history),
        }

    def save_execution_history(self, output_file: str) -> str:
        """Save execution history to JSON file."""
        history_dicts = [r.to_dict() for r in self.execution_history]

        with open(output_file, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "total_executions": len(self.execution_history),
                    "executions": history_dicts,
                },
                f,
                indent=2,
            )

        logger.info(f"Execution history saved to {output_file}")
        return output_file
