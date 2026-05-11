"""
Adaptive Context Compilation Runtime - Phase 4

Transforms the compiler from static optimization subsystems into an adaptive
cognition assembly engine that dynamically allocates token budgets, selects
compression strategies, and optimizes context for provider-specific requirements.

Architecture:
- AdaptiveCompilationPlanner: Orchestrates compilation decisions
- RelevanceRankingService: Multi-factor relevance scoring
- TokenBudgetAllocator: Dynamic token distribution
- ContextQualityEvaluator: Context quality measurement
- ContextFailureAnalyzer: Regression and failure tracking
- AdaptiveAssemblyPipeline: End-to-end compilation runtime
"""

from __future__ import annotations

from typing import List, Dict, Optional, Tuple, Set, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np
import logging
from collections import defaultdict

if TYPE_CHECKING:
    from app.compiler.semantic_chunking import SemanticChunk
    from app.compiler.context_compression import CompressedContext
    from app.db.models import Memory

logger = logging.getLogger(__name__)


class QueryComplexity(str, Enum):
    """Query complexity assessment."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    RESEARCH_INTENSIVE = "research_intensive"


@dataclass
class RankingFactors:
    """Factors used in relevance ranking."""

    semantic_similarity: float = 0.0
    importance_score: float = 0.0
    recency_score: float = 0.0
    reasoning_continuity: float = 0.0
    workspace_relevance: float = 0.0
    provider_fit: float = 0.0
    information_density: float = 0.0

    # Weights (normalized to sum to 1.0)
    weights: Dict[str, float] = field(
        default_factory=lambda: {
            "semantic_similarity": 0.35,
            "importance_score": 0.20,
            "recency_score": 0.15,
            "reasoning_continuity": 0.15,
            "workspace_relevance": 0.10,
            "provider_fit": 0.03,
            "information_density": 0.02,
        }
    )

    def compute_score(self) -> float:
        """Compute weighted relevance score."""
        score = (
            self.semantic_similarity * self.weights["semantic_similarity"]
            + self.importance_score * self.weights["importance_score"]
            + self.recency_score * self.weights["recency_score"]
            + self.reasoning_continuity * self.weights["reasoning_continuity"]
            + self.workspace_relevance * self.weights["workspace_relevance"]
            + self.provider_fit * self.weights["provider_fit"]
            + self.information_density * self.weights["information_density"]
        )
        return min(1.0, max(0.0, score))


@dataclass
class CompilationPlan:
    """Plan for adaptive context compilation."""

    query: str = ""
    selected_memories: List[str] = field(default_factory=list)
    selected_chunks: List[str] = field(default_factory=list)

    # Token allocation
    total_budget: int = 0
    allocated_tokens: Dict[str, int] = field(default_factory=dict)  # category -> tokens
    remaining_budget: int = 0

    # Compression decisions
    compression_mode: str = "compressed"
    compression_ratios: Dict[str, float] = field(default_factory=dict)

    # Quality metrics
    estimated_quality: float = 0.0
    semantic_density: float = 0.0
    reasoning_preservation: float = 0.0

    # Ranking details
    ranked_items: List[Tuple[str, float]] = field(
        default_factory=list
    )  # (item_id, score)
    ranking_explanations: Dict[str, str] = field(default_factory=dict)

    # Metadata
    planning_time_ms: float = 0.0
    provider: str = "generic"
    query_complexity: str = QueryComplexity.MODERATE.value


@dataclass
class TokenAllocation:
    """Token allocation breakdown."""

    active_reasoning: int = 0
    semantic_memories: int = 0
    workspace_summary: int = 0
    chunk_summaries: int = 0
    metadata_glue: int = 0
    compression_buffer: int = 0

    def total(self) -> int:
        """Get total allocated tokens."""
        return (
            self.active_reasoning
            + self.semantic_memories
            + self.workspace_summary
            + self.chunk_summaries
            + self.metadata_glue
            + self.compression_buffer
        )

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            "active_reasoning": self.active_reasoning,
            "semantic_memories": self.semantic_memories,
            "workspace_summary": self.workspace_summary,
            "chunk_summaries": self.chunk_summaries,
            "metadata_glue": self.metadata_glue,
            "compression_buffer": self.compression_buffer,
        }


@dataclass
class ContextQualityScore:
    """Comprehensive context quality evaluation."""

    semantic_density: float = 0.0  # Semantic value per token
    redundancy_score: float = 0.0  # 0=no redundancy, 1=highly redundant
    entity_continuity: float = 0.0  # Entity tracking across context
    reasoning_preservation: float = 0.0  # Reasoning chain integrity
    topic_preservation: float = 0.0  # Topic coherence
    provider_compatibility: float = 0.0  # Fit for target provider
    compression_effectiveness: float = 0.0  # Quality of compression

    # Composite score
    overall_quality: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "semantic_density": self.semantic_density,
            "redundancy_score": self.redundancy_score,
            "entity_continuity": self.entity_continuity,
            "reasoning_preservation": self.reasoning_preservation,
            "topic_preservation": self.topic_preservation,
            "provider_compatibility": self.provider_compatibility,
            "compression_effectiveness": self.compression_effectiveness,
            "overall_quality": self.overall_quality,
        }


@dataclass
class CompilationFailureRecord:
    """Record of compilation failure for regression analysis."""

    timestamp: datetime = field(default_factory=datetime.utcnow)
    failure_type: str = ""  # semantic_drift, hallucination, reasoning_collapse, etc.
    severity: float = 0.0  # 0-1 scale
    description: str = ""

    # Context that led to failure
    query: str = ""
    provider: str = ""
    compression_mode: str = ""
    token_budget: int = 0

    # Recovery data
    recovered: bool = False
    recovery_strategy: str = ""


class RelevanceRankingService:
    """Multi-factor relevance ranking service."""

    def __init__(self):
        """Initialize ranking service."""
        self.ranking_history: List[Dict] = []

    def rank_memories(
        self,
        memories: List["Memory"],
        query: str,
        workspace_context: Optional[Dict] = None,
        provider: str = "generic",
    ) -> List[Tuple["Memory", float, RankingFactors]]:
        """
        Rank memories by relevance using multi-factor scoring.

        Args:
            memories: List of memories to rank
            query: User query
            workspace_context: Current workspace state
            provider: Target provider for optimization

        Returns:
            List of (memory, score, factors) tuples
        """
        import time

        start_time = time.time()

        ranked = []

        for memory in memories:
            factors = RankingFactors()

            # Semantic similarity (main factor)
            factors.semantic_similarity = self._compute_semantic_similarity(
                memory, query
            )

            # Importance score
            factors.importance_score = getattr(memory, "importance_score", 0.5)

            # Recency (recent memories score higher)
            factors.recency_score = self._compute_recency_score(memory)

            # Reasoning continuity
            factors.reasoning_continuity = self._compute_reasoning_continuity(
                memory, query
            )

            # Workspace relevance
            factors.workspace_relevance = self._compute_workspace_relevance(
                memory, workspace_context
            )

            # Provider-specific fit
            factors.provider_fit = self._compute_provider_fit(memory, provider)

            # Information density
            factors.information_density = self._compute_information_density(memory)

            # Compute final score
            score = factors.compute_score()
            ranked.append((memory, score, factors))

        # Sort by score descending
        ranked.sort(key=lambda x: x[1], reverse=True)

        # Record ranking
        self.ranking_history.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "query": query,
                "provider": provider,
                "time_ms": (time.time() - start_time) * 1000,
                "num_memories": len(memories),
                "top_score": ranked[0][1] if ranked else 0.0,
            }
        )

        return ranked

    def _compute_semantic_similarity(self, memory: "Memory", query: str) -> float:
        """Compute semantic similarity between memory and query."""
        # Rough approximation: word overlap
        query_words = set(query.lower().split())
        memory_words = set(getattr(memory, "raw_content", "").lower().split())

        if not query_words:
            return 0.5

        overlap = len(query_words & memory_words) / len(query_words)
        return min(1.0, overlap)

    def _compute_recency_score(self, memory: "Memory") -> float:
        """Compute recency score (newer memories score higher)."""
        if not hasattr(memory, "timestamp"):
            return 0.5

        # Simple approach: exponential decay from recent
        now = datetime.utcnow()
        age_hours = (now - memory.timestamp).total_seconds() / 3600

        # Decay factor: halves every 24 hours
        decay = 0.5 ** (age_hours / 24)
        return decay

    def _compute_reasoning_continuity(self, memory: "Memory", query: str) -> float:
        """Score memory for reasoning chain preservation."""
        content = getattr(memory, "raw_content", "")

        # Check for logical connectors
        logical_connectors = ["because", "therefore", "thus", "hence", "if", "then"]
        connector_count = sum(
            1 for conn in logical_connectors if conn in content.lower()
        )

        return min(1.0, connector_count / 3.0)

    def _compute_workspace_relevance(
        self, memory: "Memory", workspace_context: Optional[Dict]
    ) -> float:
        """Score memory for workspace context relevance."""
        if not workspace_context:
            return 0.5

        # Check if memory relates to current workspace items
        workspace_items = workspace_context.get("active_items", [])
        memory_content = getattr(memory, "raw_content", "").lower()

        matches = sum(1 for item in workspace_items if item.lower() in memory_content)
        return min(1.0, matches / max(1, len(workspace_items)))

    def _compute_provider_fit(self, memory: "Memory", provider: str) -> float:
        """Score memory for provider-specific optimization."""
        content = getattr(memory, "raw_content", "")

        if provider == "claude":
            # Claude prefers structured, reasoned content
            has_structure = any(char in content for char in [":", "-", "•"])
            return 0.7 if has_structure else 0.3
        elif provider == "openai":
            # GPT prefers concise, direct statements
            is_concise = len(content) < 500
            return 0.7 if is_concise else 0.3
        elif provider == "gemini":
            # Gemini prefers balanced, comprehensive content
            is_balanced = 50 < len(content) < 1000
            return 0.7 if is_balanced else 0.3
        else:
            return 0.5

    def _compute_information_density(self, memory: "Memory") -> float:
        """Score memory for information density."""
        content = getattr(memory, "raw_content", "")

        if not content:
            return 0.0

        # Higher density = more unique words per content length
        words = set(content.lower().split())
        unique_ratio = len(words) / max(1, len(content.split()))

        return min(1.0, unique_ratio)


class TokenBudgetAllocator:
    """Dynamic token budget allocation engine."""

    def __init__(self):
        """Initialize allocator."""
        self.allocation_history: List[Dict] = []

    def allocate_budget(
        self,
        total_budget: int,
        num_memories: int,
        num_chunks: int,
        compression_mode: str = "compressed",
        provider: str = "generic",
    ) -> TokenAllocation:
        """
        Intelligently allocate token budget across compilation stages.

        Args:
            total_budget: Total token budget available
            num_memories: Number of selected memories
            num_chunks: Number of semantic chunks
            compression_mode: Compression strategy
            provider: Target provider

        Returns:
            TokenAllocation breakdown
        """
        allocation = TokenAllocation()

        # Base allocation percentages (tuned through benchmarking)
        allocation.metadata_glue = int(total_budget * 0.05)  # 5% for glue
        allocation.compression_buffer = int(total_budget * 0.05)  # 5% buffer

        remaining = (
            total_budget - allocation.metadata_glue - allocation.compression_buffer
        )

        # Provider-specific adjustments
        if provider == "claude":
            # Claude benefits from structured reasoning context
            allocation.active_reasoning = int(remaining * 0.30)
            allocation.workspace_summary = int(remaining * 0.25)
            allocation.semantic_memories = int(remaining * 0.35)
            allocation.chunk_summaries = int(remaining * 0.10)
        elif provider == "openai":
            # GPT prefers concise operational context
            allocation.active_reasoning = int(remaining * 0.25)
            allocation.workspace_summary = int(remaining * 0.15)
            allocation.semantic_memories = int(remaining * 0.50)
            allocation.chunk_summaries = int(remaining * 0.10)
        elif provider == "gemini":
            # Gemini prefers balanced coverage
            allocation.active_reasoning = int(remaining * 0.25)
            allocation.workspace_summary = int(remaining * 0.20)
            allocation.semantic_memories = int(remaining * 0.40)
            allocation.chunk_summaries = int(remaining * 0.15)
        else:
            # Generic allocation
            allocation.active_reasoning = int(remaining * 0.25)
            allocation.workspace_summary = int(remaining * 0.20)
            allocation.semantic_memories = int(remaining * 0.40)
            allocation.chunk_summaries = int(remaining * 0.15)

        # Compression mode adjustments
        if compression_mode == "minimal":
            # Minimal compression needs more buffer
            allocation.compression_buffer = int(total_budget * 0.10)
        elif compression_mode == "full_context":
            # Full context needs less compression
            allocation.compression_buffer = int(total_budget * 0.02)

        # Record allocation
        self.allocation_history.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "total_budget": total_budget,
                "allocation": allocation.to_dict(),
                "provider": provider,
                "compression_mode": compression_mode,
            }
        )

        return allocation

    def get_allocation_ratio(self, category: str, total_budget: int) -> float:
        """Get allocation ratio for a category as percentage of budget."""
        allocation = self.allocate_budget(total_budget, 1, 1)
        allocated = allocation.to_dict().get(category, 0)
        return allocated / total_budget if total_budget > 0 else 0.0


class ContextQualityEvaluator:
    """Comprehensive context quality evaluation."""

    def __init__(self):
        """Initialize evaluator."""
        self.quality_history: List[Dict] = []

    def evaluate_context(
        self,
        compiled_context: str,
        original_memories: List["Memory"],
        compression_ratio: float,
        provider: str = "generic",
    ) -> ContextQualityScore:
        """
        Evaluate quality of compiled context.

        Args:
            compiled_context: Final compiled context string
            original_memories: Original memories that were compiled
            compression_ratio: Achieved compression ratio
            provider: Target provider

        Returns:
            ContextQualityScore with all metrics
        """
        score = ContextQualityScore()

        # Semantic density (semantic value per token)
        score.semantic_density = self._compute_semantic_density(
            compiled_context, original_memories
        )

        # Redundancy (lower is better)
        score.redundancy_score = self._compute_redundancy(compiled_context)

        # Entity continuity
        score.entity_continuity = self._compute_entity_continuity(
            compiled_context, original_memories
        )

        # Reasoning preservation
        score.reasoning_preservation = self._compute_reasoning_preservation(
            compiled_context, original_memories
        )

        # Topic preservation
        score.topic_preservation = self._compute_topic_preservation(
            compiled_context, original_memories
        )

        # Provider compatibility
        score.provider_compatibility = self._compute_provider_compatibility(
            compiled_context, provider
        )

        # Compression effectiveness (how well we used compression)
        score.compression_effectiveness = min(1.0, 1.0 - compression_ratio)

        # Composite score (weighted average)
        score.overall_quality = (
            score.semantic_density * 0.30
            + (1.0 - score.redundancy_score) * 0.10
            + score.entity_continuity * 0.15
            + score.reasoning_preservation * 0.20
            + score.topic_preservation * 0.15
            + score.provider_compatibility * 0.10
        )

        # Record evaluation
        self.quality_history.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "quality_scores": score.to_dict(),
                "provider": provider,
                "compression_ratio": compression_ratio,
            }
        )

        return score

    def _compute_semantic_density(
        self, context: str, original_memories: List["Memory"]
    ) -> float:
        """Semantic value per token in context."""
        if not context or not original_memories:
            return 0.5

        # Rough measure: unique concepts per token
        unique_words = set(context.lower().split())
        tokens = len(context) // 4  # Rough token estimate

        density = len(unique_words) / max(1, tokens)
        return min(1.0, density)

    def _compute_redundancy(self, context: str) -> float:
        """Measure redundancy in context (lower is better)."""
        lines = context.split("\n")

        if len(lines) < 2:
            return 0.0

        # Measure line similarity
        total_similarity = 0.0
        comparisons = 0

        for i, line1 in enumerate(lines[:5]):  # Sample first 5 lines
            for line2 in lines[i + 1 : 5]:
                # Simple word overlap
                words1 = set(line1.lower().split())
                words2 = set(line2.lower().split())

                if words1 and words2:
                    overlap = len(words1 & words2) / len(words1 | words2)
                    total_similarity += overlap
                    comparisons += 1

        return total_similarity / max(1, comparisons)

    def _compute_entity_continuity(
        self, context: str, original_memories: List["Memory"]
    ) -> float:
        """Track entity coherence across context."""
        import re

        # Extract named entities (capitalized words)
        entities = set(re.findall(r"\b[A-Z][a-z]+\b", context))

        # Extract from originals
        original_entities = set()
        for mem in original_memories:
            content = getattr(mem, "raw_content", "")
            original_entities.update(re.findall(r"\b[A-Z][a-z]+\b", content))

        if not original_entities:
            return 0.5

        retained = len(entities & original_entities) / len(original_entities)
        return retained

    def _compute_reasoning_preservation(
        self, context: str, original_memories: List["Memory"]
    ) -> float:
        """Measure preservation of reasoning chains."""
        logical_terms = ["because", "therefore", "thus", "hence", "if", "then"]

        # Count in compiled
        compiled_logic = sum(1 for term in logical_terms if term in context.lower())

        # Count in originals
        original_logic = 0
        for mem in original_memories:
            content = getattr(mem, "raw_content", "").lower()
            original_logic += sum(1 for term in logical_terms if term in content)

        if original_logic == 0:
            return 1.0

        return min(1.0, compiled_logic / original_logic)

    def _compute_topic_preservation(
        self, context: str, original_memories: List["Memory"]
    ) -> float:
        """Measure topic coherence preservation."""
        from collections import Counter
        import re

        # Extract frequent words (topics)
        words = re.findall(r"\b[a-z]{4,}\b", context.lower())
        topics = set([w for w, c in Counter(words).most_common(5)])

        # Extract from originals
        original_topics = set()
        for mem in original_memories:
            content = getattr(mem, "raw_content", "").lower()
            words = re.findall(r"\b[a-z]{4,}\b", content)
            original_topics.update([w for w, c in Counter(words).most_common(3)])

        if not original_topics:
            return 0.5

        retained = len(topics & original_topics) / len(original_topics)
        return retained

    def _compute_provider_compatibility(self, context: str, provider: str) -> float:
        """Measure compatibility with target provider's preferences."""
        length = len(context)

        if provider == "claude":
            # Claude prefers structured, reasoned content (500-2000 chars)
            is_good_length = 500 < length < 2000
            has_structure = any(c in context for c in [":", "-", "•"])
            return 0.9 if (is_good_length and has_structure) else 0.5
        elif provider == "openai":
            # GPT prefers concise content
            is_concise = length < 1000
            return 0.9 if is_concise else 0.5
        elif provider == "gemini":
            # Gemini prefers balanced coverage
            is_balanced = 200 < length < 2000
            return 0.9 if is_balanced else 0.5
        else:
            return 0.7


class ContextFailureAnalyzer:
    """Tracks and analyzes compilation failures for regression detection."""

    def __init__(self):
        """Initialize analyzer."""
        self.failure_records: List[CompilationFailureRecord] = []
        self.failure_trends: Dict[str, int] = defaultdict(int)

    def record_failure(
        self,
        failure_type: str,
        severity: float,
        query: str,
        provider: str,
        compression_mode: str,
        token_budget: int,
        description: str = "",
    ) -> None:
        """
        Record a compilation failure.

        Args:
            failure_type: Type of failure (semantic_drift, hallucination, etc.)
            severity: Severity score (0-1)
            query: Query that led to failure
            provider: Provider used
            compression_mode: Compression mode used
            token_budget: Token budget used
            description: Detailed description
        """
        record = CompilationFailureRecord(
            failure_type=failure_type,
            severity=severity,
            description=description,
            query=query,
            provider=provider,
            compression_mode=compression_mode,
            token_budget=token_budget,
        )

        self.failure_records.append(record)
        self.failure_trends[failure_type] += 1

    def get_regression_report(self) -> Dict:
        """Generate regression analysis report."""
        if not self.failure_records:
            return {"status": "no_failures", "total_records": 0}

        # Categorize failures
        by_type = defaultdict(list)
        for record in self.failure_records:
            by_type[record.failure_type].append(record)

        # Calculate statistics
        avg_severity = np.mean([r.severity for r in self.failure_records])
        recent_failures = [
            r
            for r in self.failure_records
            if (datetime.utcnow() - r.timestamp).total_seconds() < 3600
        ]

        return {
            "total_failures": len(self.failure_records),
            "recent_failures": len(recent_failures),
            "failure_types": dict(self.failure_trends),
            "average_severity": float(avg_severity),
            "by_type": {ftype: len(records) for ftype, records in by_type.items()},
        }


class AdaptiveCompilationPlanner:
    """Orchestrates adaptive context compilation."""

    def __init__(
        self,
        ranking_service: Optional[RelevanceRankingService] = None,
        allocator: Optional[TokenBudgetAllocator] = None,
        quality_evaluator: Optional[ContextQualityEvaluator] = None,
        failure_analyzer: Optional[ContextFailureAnalyzer] = None,
    ):
        """Initialize planner with services."""
        self.ranking_service = ranking_service or RelevanceRankingService()
        self.allocator = allocator or TokenBudgetAllocator()
        self.quality_evaluator = quality_evaluator or ContextQualityEvaluator()
        self.failure_analyzer = failure_analyzer or ContextFailureAnalyzer()

        self.compilation_history: List[CompilationPlan] = []

    def plan_compilation(
        self,
        query: str,
        memories: List["Memory"],
        chunks: List["SemanticChunk"],
        token_budget: int,
        provider: str = "generic",
        workspace_context: Optional[Dict] = None,
    ) -> CompilationPlan:
        """
        Create adaptive compilation plan.

        Args:
            query: User query
            memories: Available memories
            chunks: Available semantic chunks
            token_budget: Total token budget
            provider: Target provider
            workspace_context: Current workspace state

        Returns:
            CompilationPlan with optimized decisions
        """
        import time

        start_time = time.time()

        plan = CompilationPlan(
            query=query,
            total_budget=token_budget,
            provider=provider,
        )

        # Step 1: Assess query complexity
        plan.query_complexity = self._assess_query_complexity(query)

        # Step 2: Rank memories and chunks
        ranked_memories = self.ranking_service.rank_memories(
            memories, query, workspace_context, provider
        )

        # Step 3: Select top memories based on budget
        plan.ranked_items = [(m.id, score) for m, score, _ in ranked_memories]

        # Estimate budget needed
        max_memories = min(
            len(memories),
            int(token_budget * 0.30 / 50),  # ~50 tokens per memory
        )

        plan.selected_memories = [m.id for m, _, _ in ranked_memories[:max_memories]]

        # Step 4: Select complementary chunks
        plan.selected_chunks = [c.chunk_id for c in chunks[:5]]

        # Step 5: Allocate token budget
        allocation = self.allocator.allocate_budget(
            token_budget,
            len(plan.selected_memories),
            len(plan.selected_chunks),
            compression_mode=plan.compression_mode,
            provider=provider,
        )

        plan.allocated_tokens = allocation.to_dict()
        plan.remaining_budget = max(0, token_budget - allocation.total())

        # Step 6: Select compression mode adaptively
        plan.compression_mode = self._select_compression_mode(
            token_budget,
            plan.query_complexity,
            provider,
        )

        # Step 7: Estimate compilation quality
        plan.semantic_density = len(plan.selected_memories) / max(1, token_budget / 50)
        plan.reasoning_preservation = self._estimate_reasoning_preservation(
            [m for m in memories if m.id in plan.selected_memories]
        )

        # Estimate overall quality
        plan.estimated_quality = (
            plan.semantic_density * 0.5 + plan.reasoning_preservation * 0.5
        )

        # Record plan
        plan.planning_time_ms = (time.time() - start_time) * 1000
        self.compilation_history.append(plan)

        return plan

    def _assess_query_complexity(self, query: str) -> str:
        """Assess query complexity."""
        words = len(query.split())

        if words < 5:
            return QueryComplexity.SIMPLE.value
        elif words < 15:
            return QueryComplexity.MODERATE.value
        elif words < 50:
            return QueryComplexity.COMPLEX.value
        else:
            return QueryComplexity.RESEARCH_INTENSIVE.value

    def _select_compression_mode(
        self,
        token_budget: int,
        query_complexity: str,
        provider: str,
    ) -> str:
        """Select compression mode adaptively."""
        # Smaller budget requires more compression
        if token_budget < 1000:
            return "minimal"
        elif token_budget < 2000:
            if query_complexity == QueryComplexity.SIMPLE.value:
                return "minimal"
            else:
                return "compressed"
        elif token_budget < 4000:
            if query_complexity == QueryComplexity.RESEARCH_INTENSIVE.value:
                return "research_mode"
            else:
                return "compressed"
        else:
            if query_complexity == QueryComplexity.RESEARCH_INTENSIVE.value:
                return "research_mode"
            else:
                return "full_context"

    def _estimate_reasoning_preservation(
        self, selected_memories: List["Memory"]
    ) -> float:
        """Estimate reasoning preservation from selected memories."""
        if not selected_memories:
            return 0.5

        logical_terms = ["because", "therefore", "thus", "if", "then"]
        has_logic = 0

        for mem in selected_memories:
            content = getattr(mem, "raw_content", "").lower()
            if any(term in content for term in logical_terms):
                has_logic += 1

        return min(1.0, has_logic / len(selected_memories))
