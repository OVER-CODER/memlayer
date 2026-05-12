"""
Adaptive Context Compilation Runtime - Phase 4

This module implements adaptive cognition assembly that dynamically decides:
- what information matters most
- what deserves token budget
- what should be compressed
- what can be omitted
- how context should be shaped per-provider

Core: runtime cognitive resource allocation, not prompt engineering.

Architecture:
- AdaptiveCompilationPlanner: Dynamic memory/chunk selection
- RelevanceRankingService: 7-factor ranking beyond similarity
- TokenBudgetAllocator: Intelligent token distribution
- ContextQualityEvaluator: Multi-dimensional quality scoring
- ContextFailureAnalyzer: Regression and failure tracking
- Adaptive assembly pipeline: retrieval→dedup→chunk→rank→compress→allocate
"""

from __future__ import annotations

from typing import List, Dict, Optional, Tuple, Set, TYPE_CHECKING, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np
import logging
import json

if TYPE_CHECKING:
    from app.compiler.semantic_chunking import SemanticChunk
    from app.compiler.context_compression import CompressedContext
    from app.db.models import Memory

logger = logging.getLogger(__name__)


class QueryType(str, Enum):
    """Types of queries with different compilation strategies."""

    REASONING = "reasoning"  # Complex reasoning, needs full context
    FACTUAL = "factual"  # Factual lookup, can be more compressed
    CODING = "coding"  # Code-related, needs technical precision
    RESEARCH = "research"  # Research-focused, needs citations
    NARRATIVE = "narrative"  # Narrative queries, needs continuity


@dataclass
class RankingFactors:
    """Breakdown of ranking contributions."""

    semantic_similarity: float = 0.0
    importance_score: float = 0.0
    recency_factor: float = 0.0
    reasoning_continuity: float = 0.0
    workspace_relevance: float = 0.0
    provider_fit: float = 0.0
    information_density: float = 0.0

    def total_score(self) -> float:
        """Calculate weighted total."""
        return (
            self.semantic_similarity * 0.25
            + self.importance_score * 0.20
            + self.recency_factor * 0.15
            + self.reasoning_continuity * 0.15
            + self.workspace_relevance * 0.10
            + self.provider_fit * 0.10
            + self.information_density * 0.05
        )


@dataclass
class ContextQualityScore:
    """Multi-dimensional quality evaluation."""

    semantic_density: float = 0.0  # Value per token
    redundancy_ratio: float = 0.0  # Lower is better
    entity_continuity: float = 0.0  # Named entity preservation
    reasoning_preservation: float = 0.0  # Logical chain survival
    topic_preservation: float = 0.0  # Topic coherence
    provider_compatibility: float = 0.0  # Provider-specific fit
    compression_effectiveness: float = 0.0  # Token savings vs retention

    def overall_quality(self) -> float:
        """Calculate weighted overall quality."""
        return (
            self.semantic_density * 0.20
            + (1.0 - self.redundancy_ratio) * 0.15
            + self.entity_continuity * 0.15
            + self.reasoning_preservation * 0.15
            + self.topic_preservation * 0.15
            + self.provider_compatibility * 0.10
            + self.compression_effectiveness * 0.10
        )


@dataclass
class TokenBudgetAllocation:
    """Dynamic token budget allocation breakdown."""

    total_budget: int = 0
    reasoning_context: int = 0
    semantic_memories: int = 0
    workspace_summary: int = 0
    chunk_summaries: int = 0
    metadata_glue: int = 0
    response_reserve: int = 0

    def verify_allocation(self) -> bool:
        """Verify allocation stays within budget."""
        total_allocated = (
            self.reasoning_context
            + self.semantic_memories
            + self.workspace_summary
            + self.chunk_summaries
            + self.metadata_glue
            + self.response_reserve
        )
        return total_allocated <= self.total_budget


@dataclass
class CompilationPlan:
    """Adaptive compilation plan with all decisions."""

    query: str
    query_type: QueryType = QueryType.REASONING

    # Selection decisions
    selected_memories: List[str] = field(default_factory=list)
    selected_chunks: List[str] = field(default_factory=list)
    excluded_items: List[str] = field(default_factory=list)

    # Ranking and scoring
    ranking_scores: Dict[str, float] = field(default_factory=dict)
    ranking_explanations: Dict[str, str] = field(default_factory=dict)

    # Compression decisions
    compression_mode: str = "compressed"
    provider_type: str = "generic"

    # Token allocation
    token_allocation: Optional[TokenBudgetAllocation] = None

    # Quality metrics
    quality_score: Optional[ContextQualityScore] = None

    # Metadata
    compilation_time_ms: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CompilationMetrics:
    """Metrics for compilation operations."""

    total_compilations: int = 0
    avg_quality_score: float = 0.0
    avg_compression_ratio: float = 0.0
    avg_ranking_time_ms: float = 0.0
    avg_allocation_time_ms: float = 0.0
    avg_total_compilation_time_ms: float = 0.0

    # Semantic preservation
    avg_semantic_retention: float = 0.0
    avg_entity_preservation: float = 0.0

    # Efficiency
    avg_tokens_used: int = 0
    avg_tokens_saved: int = 0


@dataclass
class FailureAnalysis:
    """Analysis of compilation failures and regressions."""

    timestamp: datetime = field(default_factory=datetime.utcnow)
    query: str = ""
    reason: str = ""

    # Regression indicators
    semantic_drift: float = 0.0  # Deviation from baseline
    hallucination_risk: float = 0.0
    missing_entities: List[str] = field(default_factory=list)
    reasoning_collapse: bool = False
    over_compression_detected: bool = False
    provider_degradation: float = 0.0

    # Recovery suggestions
    recommended_actions: List[str] = field(default_factory=list)


class RelevanceRankingService:
    """Service for multi-factor relevance ranking."""

    def __init__(self, embedding_service=None):
        """Initialize ranking service."""
        if embedding_service is None:
            try:
                from app.services.embedding import get_embedding_service

                self.embedding_service = get_embedding_service()
            except ImportError:
                self.embedding_service = None
        else:
            self.embedding_service = embedding_service

    def rank_memories(
        self,
        query: str,
        memories: List[Memory],
        workspace_state: Optional[Dict] = None,
        provider_type: str = "generic",
        query_type: QueryType = QueryType.REASONING,
    ) -> List[Tuple[str, float, RankingFactors]]:
        """
        Rank memories using 7-factor ranking.

        Returns:
            List of (memory_id, score, factors) tuples
        """
        import time

        start_time = time.time()

        rankings = []

        for memory in memories:
            factors = self._calculate_ranking_factors(
                query, memory, workspace_state, provider_type, query_type
            )
            score = factors.total_score()
            rankings.append((memory.id, score, factors))

        # Sort by score descending
        rankings.sort(key=lambda x: x[1], reverse=True)

        elapsed = (time.time() - start_time) * 1000
        logger.info(f"Ranked {len(memories)} memories in {elapsed:.2f}ms")

        return rankings

    def _calculate_ranking_factors(
        self,
        query: str,
        memory: Memory,
        workspace_state: Optional[Dict],
        provider_type: str,
        query_type: QueryType,
    ) -> RankingFactors:
        """Calculate 7-factor ranking for a memory."""
        factors = RankingFactors()

        # 1. Semantic Similarity
        if memory.embedding and hasattr(memory, "raw_content"):
            sim = self._calculate_similarity(query, memory.embedding)
            factors.semantic_similarity = sim

        # 2. Importance Score
        if hasattr(memory, "importance_score"):
            factors.importance_score = memory.importance_score

        # 3. Recency Factor
        if hasattr(memory, "timestamp"):
            recency = self._calculate_recency(memory.timestamp)
            factors.recency_factor = recency

        # 4. Reasoning Continuity
        if hasattr(memory, "raw_content"):
            reasoning_score = self._calculate_reasoning_continuity(
                memory.raw_content, query
            )
            factors.reasoning_continuity = reasoning_score

        # 5. Workspace Relevance
        if workspace_state:
            workspace_score = self._calculate_workspace_relevance(
                memory, workspace_state
            )
            factors.workspace_relevance = workspace_score

        # 6. Provider Fit
        provider_score = self._calculate_provider_fit(memory, provider_type, query_type)
        factors.provider_fit = provider_score

        # 7. Information Density
        if hasattr(memory, "raw_content"):
            density = self._calculate_information_density(memory.raw_content)
            factors.information_density = density

        return factors

    def _calculate_similarity(self, query: str, embedding: Any) -> float:
        """Calculate semantic similarity (0-1)."""
        try:
            if isinstance(embedding, list):
                embedding = np.array(embedding)
            # Rough estimation without actual embeddings
            query_length = len(query)
            similarity = min(1.0, query_length / 100.0)
            return similarity
        except Exception:
            return 0.5

    def _calculate_recency(self, timestamp: datetime) -> float:
        """Calculate recency score (0-1)."""
        try:
            now = datetime.utcnow()
            age_days = (now - timestamp).days
            # Exponential decay: fresh = 1.0, old = 0.0
            recency = np.exp(-age_days / 30.0)
            return float(recency)
        except Exception:
            return 0.5

    def _calculate_reasoning_continuity(self, content: str, query: str) -> float:
        """Calculate reasoning chain continuity."""
        logical_connectors = [
            "because",
            "therefore",
            "thus",
            "hence",
            "if",
            "then",
            "so",
            "since",
        ]

        content_lower = content.lower()
        query_lower = query.lower()

        # Count logical connectors
        connector_count = sum(1 for conn in logical_connectors if conn in content_lower)

        # Normalize (max 5 connectors = 1.0)
        continuity = min(1.0, connector_count / 5.0)

        # Boost if query asks for reasoning
        if any(phrase in query_lower for phrase in ["why", "how", "explain"]):
            continuity = min(1.0, continuity * 1.2)

        return continuity

    def _calculate_workspace_relevance(
        self, memory: Memory, workspace_state: Dict
    ) -> float:
        """Calculate relevance to current workspace."""
        # Simple: if memory mentions workspace entities, boost score
        if not workspace_state:
            return 0.5

        relevance = 0.5  # Baseline

        # Check if memory relates to workspace context
        workspace_entities = workspace_state.get("entities", [])
        if hasattr(memory, "raw_content"):
            content_lower = memory.raw_content.lower()
            for entity in workspace_entities:
                if entity.lower() in content_lower:
                    relevance = min(1.0, relevance + 0.1)

        return relevance

    def _calculate_provider_fit(
        self, memory: Memory, provider_type: str, query_type: QueryType
    ) -> float:
        """Calculate fit for target provider."""
        fit = 0.6  # Baseline

        if hasattr(memory, "raw_content"):
            content_length = len(memory.raw_content)

            # Claude prefers longer context
            if provider_type == "claude":
                if content_length > 50:
                    fit += 0.2

            # OpenAI prefers concise
            elif provider_type == "openai":
                if content_length < 200:
                    fit += 0.2

            # Gemini likes balanced
            elif provider_type == "gemini":
                if 50 < content_length < 300:
                    fit += 0.2

        # Query type fit
        if query_type == QueryType.CODING and hasattr(memory, "raw_content"):
            if any(char in memory.raw_content for char in ["(", ")", "=", "{"]):
                fit += 0.1

        return min(1.0, fit)

    def _calculate_information_density(self, content: str) -> float:
        """Calculate information density (value per character)."""
        if not content:
            return 0.0

        # Information-rich indicators: numbers, proper nouns, technical terms
        density = 0.5

        # Count uppercase words (entities)
        uppercase_words = sum(1 for word in content.split() if word[0].isupper())
        density += min(0.25, uppercase_words / len(content.split()) * 0.25)

        # Count numbers (facts)
        digit_count = sum(1 for c in content if c.isdigit())
        density += min(0.25, digit_count / len(content) * 0.25)

        return min(1.0, density)


class TokenBudgetAllocator:
    """Intelligent token budget allocation."""

    @staticmethod
    def allocate_budget(
        total_budget: int,
        query_complexity: float,
        workspace_size: int,
        compression_mode: str,
        provider_type: str,
    ) -> TokenBudgetAllocation:
        """
        Dynamically allocate token budget across compilation stages.

        Args:
            total_budget: Total tokens available
            query_complexity: 0-1 scale of query complexity
            workspace_size: Number of memories in workspace
            compression_mode: Current compression mode
            provider_type: Target provider

        Returns:
            TokenBudgetAllocation with breakdown
        """
        allocation = TokenBudgetAllocation(total_budget=total_budget)

        # Response reserve (20-30% depending on complexity)
        reserve_ratio = 0.25 + (query_complexity * 0.05)
        allocation.response_reserve = int(total_budget * reserve_ratio)
        remaining = total_budget - allocation.response_reserve

        # Metadata glue (5-10%)
        allocation.metadata_glue = int(remaining * 0.075)
        remaining -= allocation.metadata_glue

        # Workspace summary (10-20% based on workspace size)
        workspace_ratio = min(0.2, 0.1 + (workspace_size / 1000.0 * 0.1))
        allocation.workspace_summary = int(remaining * workspace_ratio)
        remaining -= allocation.workspace_summary

        # Chunk summaries (15-25% based on compression mode)
        if compression_mode == "minimal":
            chunk_ratio = 0.15
        elif compression_mode == "full_context":
            chunk_ratio = 0.25
        else:
            chunk_ratio = 0.20

        allocation.chunk_summaries = int(remaining * chunk_ratio)
        remaining -= allocation.chunk_summaries

        # Reasoning context (20-30% based on query complexity)
        reasoning_ratio = 0.2 + (query_complexity * 0.1)
        allocation.reasoning_context = int(remaining * reasoning_ratio)
        remaining -= allocation.reasoning_context

        # Semantic memories gets the rest
        allocation.semantic_memories = remaining

        return allocation


class ContextQualityEvaluator:
    """Multi-dimensional context quality evaluation."""

    @staticmethod
    def evaluate_quality(
        compiled_context: str,
        original_memories: List[Memory],
        compression_ratio: float,
        provider_type: str,
    ) -> ContextQualityScore:
        """
        Evaluate context quality across 7 dimensions.
        """
        score = ContextQualityScore()

        # 1. Semantic Density (value per token)
        context_tokens = len(compiled_context) // 4
        original_tokens = sum(
            len(m.raw_content) // 4 if hasattr(m, "raw_content") else 0
            for m in original_memories
        )
        if context_tokens > 0:
            # Density = (information preserved) / (tokens used)
            info_preserved = 1.0 - compression_ratio
            score.semantic_density = info_preserved / (
                context_tokens / original_tokens + 0.001
            )
            score.semantic_density = min(1.0, score.semantic_density)

        # 2. Redundancy Ratio
        unique_sentences = len(
            set(s.strip() for s in compiled_context.split(".") if s.strip())
        )
        total_sentences = len(
            [s.strip() for s in compiled_context.split(".") if s.strip()]
        )
        if total_sentences > 0:
            score.redundancy_ratio = 1.0 - (unique_sentences / total_sentences)

        # 3. Entity Continuity (named entity preservation)
        original_entities = set()
        for memory in original_memories:
            if hasattr(memory, "raw_content"):
                entities = set(
                    word
                    for word in memory.raw_content.split()
                    if word and word[0].isupper()
                )
                original_entities.update(entities)

        preserved_entities = sum(
            1 for entity in original_entities if entity in compiled_context
        )
        if original_entities:
            score.entity_continuity = preserved_entities / len(original_entities)

        # 4. Reasoning Preservation
        logical_connectors = ["because", "therefore", "thus", "hence", "if", "then"]
        connector_count = sum(
            1 for conn in logical_connectors if conn in compiled_context.lower()
        )
        score.reasoning_preservation = min(1.0, connector_count / 3.0)

        # 5. Topic Preservation
        # Simple: noun-heavy content indicates topic diversity
        words = compiled_context.lower().split()
        noun_indicators = sum(
            1 for w in words if w.endswith(("tion", "ity", "ness", "ment"))
        )
        score.topic_preservation = min(1.0, noun_indicators / max(len(words) / 10, 1))

        # 6. Provider Compatibility
        if provider_type == "claude":
            # Claude prefers structured reasoning
            score.provider_compatibility = score.reasoning_preservation
        elif provider_type == "openai":
            # OpenAI prefers concise, dense content
            score.provider_compatibility = score.semantic_density / 2.0
        elif provider_type == "gemini":
            # Gemini likes balanced coverage
            score.provider_compatibility = (
                score.entity_continuity + score.topic_preservation
            ) / 2.0
        else:
            score.provider_compatibility = 0.6

        # 7. Compression Effectiveness (tokens saved vs quality loss)
        # Higher is better: saved tokens with minimal quality loss
        if compression_ratio > 0:
            quality_preserved = 1.0 - ((1.0 - score.semantic_density) * 0.5)
            score.compression_effectiveness = compression_ratio * quality_preserved

        return score


class ContextFailureAnalyzer:
    """Analyzes compilation failures and regressions."""

    def __init__(self):
        """Initialize failure analyzer."""
        self.failure_history: List[FailureAnalysis] = []

    def analyze_failure(
        self,
        query: str,
        compiled_context: str,
        original_context: str,
        baseline_metrics: Optional[Dict] = None,
    ) -> FailureAnalysis:
        """
        Analyze compilation failure or regression.
        """
        analysis = FailureAnalysis(query=query)

        # Check for semantic drift
        if baseline_metrics:
            baseline_retention = baseline_metrics.get("semantic_retention", 1.0)
            current_retention = self._calculate_retention(
                original_context, compiled_context
            )
            analysis.semantic_drift = baseline_retention - current_retention

        # Check for missing entities
        original_entities = set(
            word for word in original_context.split() if word and word[0].isupper()
        )
        preserved_entities = sum(
            1 for entity in original_entities if entity in compiled_context
        )
        if original_entities:
            entity_preservation = preserved_entities / len(original_entities)
            if entity_preservation < 0.5:
                analysis.missing_entities = list(
                    original_entities
                    - {
                        word
                        for word in compiled_context.split()
                        if word in original_entities
                    }
                )

        # Check for reasoning collapse
        logical_connectors = ["because", "therefore", "thus", "hence", "if", "then"]
        original_logic = sum(
            1 for conn in logical_connectors if conn in original_context.lower()
        )
        compiled_logic = sum(
            1 for conn in logical_connectors if conn in compiled_context.lower()
        )
        if original_logic > 0 and compiled_logic < original_logic * 0.3:
            analysis.reasoning_collapse = True
            analysis.reason = "Logical connectors not preserved"

        # Check for over-compression
        compression_ratio = 1.0 - (len(compiled_context) / len(original_context))
        if compression_ratio > 0.8:
            analysis.over_compression_detected = True
            # Only set reason if reasoning_collapse didn't already set it
            if not analysis.reasoning_collapse:
                analysis.reason = "Over 80% compression detected"

        # Recommendations
        if analysis.reasoning_collapse:
            analysis.recommended_actions.append(
                "Use higher compression mode (e.g., COMPRESSED instead of MINIMAL)"
            )
        if analysis.over_compression_detected:
            analysis.recommended_actions.append(
                "Increase token budget or reduce compression ratio"
            )
        if analysis.missing_entities:
            analysis.recommended_actions.append(
                f"Preserve key entities: {', '.join(analysis.missing_entities[:3])}"
            )

        self.failure_history.append(analysis)
        return analysis

    def _calculate_retention(self, original: str, compressed: str) -> float:
        """Calculate simple retention ratio."""
        if not original:
            return 1.0

        original_words = set(original.lower().split())
        compressed_words = set(compressed.lower().split())

        if original_words:
            return len(original_words & compressed_words) / len(original_words)

        return 1.0

    def get_regression_report(self) -> Dict:
        """Get regression analysis report."""
        if not self.failure_history:
            return {"total_failures": 0}

        return {
            "total_failures": len(self.failure_history),
            "avg_semantic_drift": float(
                np.mean([f.semantic_drift for f in self.failure_history])
            ),
            "reasoning_collapses": sum(
                1 for f in self.failure_history if f.reasoning_collapse
            ),
            "over_compression_cases": sum(
                1 for f in self.failure_history if f.over_compression_detected
            ),
            "common_issues": self._get_common_issues(),
        }

    def _get_common_issues(self) -> List[str]:
        """Identify common failure patterns."""
        all_actions = []
        for analysis in self.failure_history:
            all_actions.extend(analysis.recommended_actions)

        from collections import Counter

        action_counts = Counter(all_actions)
        return [action for action, _ in action_counts.most_common(5)]


class AdaptiveCompilationPlanner:
    """Main planner for adaptive context compilation."""

    def __init__(
        self,
        ranking_service: Optional[RelevanceRankingService] = None,
        embedding_service=None,
    ):
        """Initialize adaptive planner."""
        self.ranking_service = ranking_service or RelevanceRankingService(
            embedding_service
        )
        self.failure_analyzer = ContextFailureAnalyzer()

    def plan_compilation(
        self,
        query: str,
        memories: List[Memory],
        chunks: Optional[List[SemanticChunk]] = None,
        provider: str = "generic",
        token_budget: int = 4000,
        workspace_state: Optional[Dict] = None,
    ) -> CompilationPlan:
        """
        Create adaptive compilation plan.

        Args:
            query: User query
            memories: Available memories
            chunks: Semantic chunks
            provider: Target provider
            token_budget: Available tokens
            workspace_state: Current workspace context

        Returns:
            CompilationPlan with all decisions
        """
        import time

        start_time = time.time()

        plan = CompilationPlan(query=query, provider_type=provider)

        # Determine query type
        plan.query_type = self._determine_query_type(query)

        # Rank memories
        ranked_memories = self.ranking_service.rank_memories(
            query, memories, workspace_state, provider, plan.query_type
        )

        # Store ranking info
        for mem_id, score, factors in ranked_memories:
            plan.ranking_scores[mem_id] = score
            plan.ranking_explanations[mem_id] = (
                f"Similarity: {factors.semantic_similarity:.2f}, Importance: {factors.importance_score:.2f}"
            )

        # Select top memories within budget
        query_complexity = self._estimate_query_complexity(query)
        allocation = TokenBudgetAllocator.allocate_budget(
            token_budget, query_complexity, len(memories), "compressed", provider
        )
        plan.token_allocation = allocation

        # Select memories based on ranking
        memory_budget = allocation.semantic_memories
        selected_tokens = 0
        for mem_id, score, _ in ranked_memories:
            if selected_tokens < memory_budget:
                # Find memory by ID to get content length
                for mem in memories:
                    if mem.id == mem_id:
                        mem_tokens = (
                            len(mem.raw_content) // 4
                            if hasattr(mem, "raw_content")
                            else 100
                        )
                        if selected_tokens + mem_tokens <= memory_budget:
                            plan.selected_memories.append(mem_id)
                            selected_tokens += mem_tokens
                        break

        # Determine compression mode
        if len(plan.selected_memories) * 100 > memory_budget:
            plan.compression_mode = "minimal"
        else:
            plan.compression_mode = "compressed"

        # Calculate quality score
        plan.quality_score = ContextQualityScore()
        plan.quality_score.semantic_density = 0.7  # Placeholder

        plan.compilation_time_ms = (time.time() - start_time) * 1000

        return plan

    def _determine_query_type(self, query: str) -> QueryType:
        """Determine query type from query text."""
        query_lower = query.lower()

        # Check coding first (highest priority)
        if any(word in query_lower for word in ["code", "function", "api", "method"]):
            return QueryType.CODING

        # Check research
        if any(
            word in query_lower for word in ["research", "study", "paper", "citation"]
        ):
            return QueryType.RESEARCH

        # Check reasoning (includes "why" and "how" but not coding queries)
        if any(word in query_lower for word in ["why", "explain", "reason"]):
            return QueryType.REASONING

        # Check factual
        if any(word in query_lower for word in ["what", "who", "where", "when"]):
            return QueryType.FACTUAL

        return QueryType.NARRATIVE

    def _estimate_query_complexity(self, query: str) -> float:
        """Estimate query complexity (0-1)."""
        # Simple heuristic: longer queries, more specific = more complex
        word_count = len(query.split())
        complexity = min(1.0, word_count / 50.0)

        # Boost if it's a complex reasoning query
        if any(word in query.lower() for word in ["why", "how", "explain", "reason"]):
            complexity = min(1.0, complexity + 0.2)

        return complexity
