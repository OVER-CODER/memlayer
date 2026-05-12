"""
Context Compression Engine - Semantic compression runtime for AI cognition.

This module implements intelligent semantic compression that preserves meaning
while reducing token usage. It supports multiple compression modes optimized
for different use cases and provider preferences.

Architecture:
- Five compression modes (FULL, COMPRESSED, MINIMAL, RESEARCH, CODING)
- Hierarchical compression (workspace → chunks → memories)
- Semantic retention evaluation with entity/topic metrics
- Token budget simulation with provider-specific budgets
- Provider-aware optimization strategies
"""

from __future__ import annotations

from typing import List, Dict, Optional, Tuple, Set, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import numpy as np
import logging
import re
from collections import Counter

if TYPE_CHECKING:
    from app.compiler.semantic_chunking import SemanticChunk
    from app.db.models import Memory

logger = logging.getLogger(__name__)


class CompressionMode(str, Enum):
    """Compression modes for different use cases."""

    FULL_CONTEXT = "full_context"  # Maximum fidelity, minimal compression
    COMPRESSED = "compressed"  # Balanced token efficiency and abstraction
    MINIMAL = "minimal"  # Aggressive compression, ultra-low tokens
    RESEARCH_MODE = "research_mode"  # Preserve citations, facts, terminology
    CODING_MODE = "coding_mode"  # Preserve technical precision, APIs, code


class ProviderType(str, Enum):
    """Provider types for specialized optimization."""

    CLAUDE = "claude"
    OPENAI = "openai"
    GEMINI = "gemini"
    GENERIC = "generic"


@dataclass
class CompressedContext:
    """Represents compressed context with metadata."""

    original_tokens: int = 0
    compressed_tokens: int = 0
    compression_ratio: float = 0.0

    # Content
    summary: str = ""
    entities: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    key_relationships: List[str] = field(default_factory=list)

    # Metrics
    semantic_retention: float = 0.0
    entity_retention: float = 0.0
    topic_retention: float = 0.0
    reasoning_continuity: float = 0.0

    # Metadata
    compression_mode: CompressionMode = CompressionMode.COMPRESSED
    provider_type: ProviderType = ProviderType.GENERIC
    compression_time_ms: float = 0.0


@dataclass
class CompressionMetrics:
    """Metrics for compression operation."""

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    overall_compression_ratio: float = 0.0

    # Semantic preservation
    avg_entity_retention: float = 0.0
    avg_topic_retention: float = 0.0
    avg_semantic_retention: float = 0.0
    avg_reasoning_continuity: float = 0.0

    # Performance
    total_compression_time_ms: float = 0.0
    num_contexts_compressed: int = 0

    # Quality
    compression_stability: float = 0.0  # Variance in compression ratio


@dataclass
class SemanticRetentionEvaluation:
    """Detailed semantic retention analysis."""

    original_entities: Set[str] = field(default_factory=set)
    compressed_entities: Set[str] = field(default_factory=set)
    entity_retention: float = 0.0

    original_topics: Set[str] = field(default_factory=set)
    compressed_topics: Set[str] = field(default_factory=set)
    topic_retention: float = 0.0

    semantic_similarity: float = 0.0
    reasoning_continuity_score: float = 0.0
    information_density: float = 0.0


class ContextCompressionService:
    """Service for semantic compression of context."""

    def __init__(self, embedding_service=None):
        """Initialize compression service."""
        # Lazy load embedding service
        if embedding_service is None:
            try:
                from app.services.embedding import get_embedding_service

                self.embedding_service = get_embedding_service()
            except ImportError:
                self.embedding_service = None
        else:
            self.embedding_service = embedding_service

        # Provider-specific compression strategies
        self.provider_strategies = {
            ProviderType.CLAUDE: self._claude_compression_strategy,
            ProviderType.OPENAI: self._openai_compression_strategy,
            ProviderType.GEMINI: self._gemini_compression_strategy,
            ProviderType.GENERIC: self._generic_compression_strategy,
        }

    def compress_context(
        self,
        content: str,
        mode: CompressionMode = CompressionMode.COMPRESSED,
        provider: ProviderType = ProviderType.GENERIC,
        token_budget: Optional[int] = None,
    ) -> CompressedContext:
        """
        Compress context with specified mode and provider optimization.

        Args:
            content: Raw content to compress
            mode: Compression mode to use
            provider: Target provider for optimization
            token_budget: Optional token budget constraint

        Returns:
            CompressedContext with compression results
        """
        import time

        start_time = time.time()

        if not content or not content.strip():
            return CompressedContext()

        # Calculate original tokens (rough estimate)
        original_tokens = len(content) // 4

        # Extract entities and topics from original content
        original_evaluation = self._evaluate_semantic_content(content)

        # Apply compression based on mode
        compressed_content = self._apply_compression_mode(content, mode)

        # Apply provider-specific optimization
        strategy = self.provider_strategies.get(
            provider, self._generic_compression_strategy
        )
        optimized_content = strategy(compressed_content, mode, token_budget)

        # Calculate compressed tokens
        compressed_tokens = len(optimized_content) // 4

        # Evaluate semantic retention
        retention = self._evaluate_retention(content, optimized_content)

        result = CompressedContext(
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=1.0 - (compressed_tokens / original_tokens)
            if original_tokens > 0
            else 0.0,
            summary=optimized_content[:200],  # First 200 chars as summary
            entities=original_evaluation.compressed_entities,
            topics=original_evaluation.compressed_topics,
            semantic_retention=retention.semantic_similarity,
            entity_retention=retention.entity_retention,
            topic_retention=retention.topic_retention,
            reasoning_continuity=retention.reasoning_continuity_score,
            compression_mode=mode,
            provider_type=provider,
            compression_time_ms=(time.time() - start_time) * 1000,
        )

        return result

    def _apply_compression_mode(self, content: str, mode: CompressionMode) -> str:
        """Apply compression based on mode."""
        if mode == CompressionMode.FULL_CONTEXT:
            return self._compress_full_context(content)
        elif mode == CompressionMode.COMPRESSED:
            return self._compress_balanced(content)
        elif mode == CompressionMode.MINIMAL:
            return self._compress_minimal(content)
        elif mode == CompressionMode.RESEARCH_MODE:
            return self._compress_research(content)
        elif mode == CompressionMode.CODING_MODE:
            return self._compress_coding(content)
        else:
            return content

    def _compress_full_context(self, content: str) -> str:
        """Full context: minimal compression, maximum fidelity."""
        # Keep entire content with slight normalization
        return content.strip()

    def _compress_balanced(self, content: str) -> str:
        """Balanced: moderate abstraction, reasonable token reduction."""
        lines = content.split("\n")
        compressed_lines = []

        for line in lines:
            # Remove extra whitespace
            line = " ".join(line.split())

            # Skip very short lines (often redundant)
            if len(line) < 5:
                continue

            # Skip lines that are mostly punctuation
            if sum(c.isalnum() for c in line) / len(line) < 0.3:
                continue

            compressed_lines.append(line)

        # Keep top 70% of lines by importance (length as proxy)
        compressed_lines.sort(key=len, reverse=True)
        num_keep = max(1, int(len(compressed_lines) * 0.7))
        kept_lines = sorted(compressed_lines[:num_keep], key=lambda x: content.find(x))

        return " ".join(kept_lines)

    def _compress_minimal(self, content: str) -> str:
        """Minimal: aggressive compression, ultra-low tokens."""
        # Extract sentences
        sentences = re.split(r"[.!?]+", content)

        # Extract key terms (nouns, verbs)
        important_terms = self._extract_important_terms(content)

        # Create ultra-compact summary with key terms
        summary_parts = []
        for term in important_terms[:5]:  # Top 5 terms
            summary_parts.append(term)

        # Add first sentence if meaningful
        if sentences and len(sentences[0].strip()) > 10:
            summary_parts.insert(0, sentences[0].strip()[:50])

        return ". ".join(summary_parts)

    def _compress_research(self, content: str) -> str:
        """Research mode: preserve citations, facts, terminology."""
        lines = content.split("\n")
        research_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Preserve lines with citations (contain brackets or quotes)
            if "[" in line or '"' in line or "'" in line:
                research_lines.append(line)
            # Preserve lines with technical terms (multiple capitals or special chars)
            elif sum(c.isupper() for c in line) > 2:
                research_lines.append(line)
            # Preserve lines with numbers (facts/data)
            elif any(c.isdigit() for c in line):
                research_lines.append(line)

        # Keep up to 80% of preserved lines
        num_keep = max(1, int(len(research_lines) * 0.8))
        return " ".join(research_lines[:num_keep])

    def _compress_coding(self, content: str) -> str:
        """Coding mode: preserve technical precision, APIs, code."""
        lines = content.split("\n")
        code_lines = []

        for line in lines:
            # Preserve lines with code indicators
            if any(
                char in line for char in ["(", ")", "{", "}", "[", "]", ":", "=", "->"]
            ):
                code_lines.append(line)
            # Preserve lines with dots (method calls)
            elif "." in line and not line.strip().startswith("#"):
                code_lines.append(line)
            # Preserve lines with class/def/import keywords
            elif any(kw in line for kw in ["class ", "def ", "import ", "from "]):
                code_lines.append(line)

        return "\n".join(code_lines)

    def _extract_important_terms(self, content: str) -> List[str]:
        """Extract important terms from content."""
        # Simple approach: extract capitalized words and frequent terms
        words = re.findall(r"\b[A-Z][a-z]+\b|\b[a-z]{4,}\b", content)
        word_freq = Counter(words)
        return [term for term, _ in word_freq.most_common(10)]

    def _claude_compression_strategy(
        self, content: str, mode: CompressionMode, token_budget: Optional[int]
    ) -> str:
        """Claude-optimized compression: structured reasoning focus."""
        # Claude prefers clear logical structure
        lines = content.split("\n")
        structured_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Keep reasoning indicators
            if any(
                phrase in line
                for phrase in ["because", "therefore", "thus", "hence", "so"]
            ):
                structured_lines.append(line)
            # Keep numbered or bulleted items
            elif line[0].isdigit() or line[0] in "-•*":
                structured_lines.append(line)
            # Keep substantive lines
            elif len(line) > 15:
                structured_lines.append(line)

        if token_budget:
            # Respect token budget
            current_tokens = len(" ".join(structured_lines)) // 4
            if current_tokens > token_budget:
                keep_ratio = token_budget / current_tokens
                num_keep = max(1, int(len(structured_lines) * keep_ratio))
                structured_lines = structured_lines[:num_keep]

        return "\n".join(structured_lines)

    def _openai_compression_strategy(
        self, content: str, mode: CompressionMode, token_budget: Optional[int]
    ) -> str:
        """GPT-optimized compression: concise operational context."""
        # GPT prefers concise, direct statements
        sentences = re.split(r"[.!?]+", content)

        compressed = []
        for sent in sentences:
            sent = sent.strip()
            if not sent or len(sent) < 5:
                continue

            # Keep sentences under 20 words (concise)
            words = sent.split()
            if len(words) <= 20:
                compressed.append(sent)

        if token_budget:
            current_tokens = len(". ".join(compressed)) // 4
            if current_tokens > token_budget:
                keep_ratio = token_budget / current_tokens
                num_keep = max(1, int(len(compressed) * keep_ratio))
                compressed = compressed[:num_keep]

        return ". ".join(compressed)

    def _gemini_compression_strategy(
        self, content: str, mode: CompressionMode, token_budget: Optional[int]
    ) -> str:
        """Gemini-optimized compression: balanced contextual summaries."""
        # Gemini prefers balanced, comprehensive coverage
        lines = content.split("\n")
        balanced_lines = []

        # Keep diverse lines: mix of different lengths and types
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Keep every nth line for balance (simple approach)
            if i % 2 == 0 or len(line) > 30:
                balanced_lines.append(line)

        if token_budget:
            current_tokens = len(" ".join(balanced_lines)) // 4
            if current_tokens > token_budget:
                keep_ratio = token_budget / current_tokens
                num_keep = max(1, int(len(balanced_lines) * keep_ratio))
                balanced_lines = balanced_lines[:num_keep]

        return " ".join(balanced_lines)

    def _generic_compression_strategy(
        self, content: str, mode: CompressionMode, token_budget: Optional[int]
    ) -> str:
        """Generic compression: standard approach."""
        if token_budget:
            current_tokens = len(content) // 4
            if current_tokens > token_budget:
                keep_ratio = token_budget / current_tokens
                keep_chars = int(len(content) * keep_ratio)
                return content[:keep_chars]
        return content

    def _evaluate_semantic_content(self, content: str) -> SemanticRetentionEvaluation:
        """Extract entities and topics from content."""
        entities = set(re.findall(r"\b[A-Z][a-z]+\b", content))

        # Simple topic extraction (frequent words)
        words = re.findall(r"\b[a-z]{4,}\b", content.lower())
        word_freq = Counter(words)
        topics = set([word for word, _ in word_freq.most_common(5)])

        return SemanticRetentionEvaluation(
            original_entities=entities,
            original_topics=topics,
        )

    def _evaluate_retention(
        self, original: str, compressed: str
    ) -> SemanticRetentionEvaluation:
        """Evaluate semantic retention after compression."""
        original_eval = self._evaluate_semantic_content(original)
        compressed_eval = self._evaluate_semantic_content(compressed)

        # Entity retention
        if original_eval.original_entities:
            retained_entities = (
                original_eval.original_entities & compressed_eval.compressed_entities
            )
            entity_retention = len(retained_entities) / len(
                original_eval.original_entities
            )
        else:
            entity_retention = 1.0

        # Topic retention
        if original_eval.original_topics:
            retained_topics = (
                original_eval.original_topics & compressed_eval.compressed_topics
            )
            topic_retention = len(retained_topics) / len(original_eval.original_topics)
        else:
            topic_retention = 1.0

        # Semantic similarity (rough: based on word overlap)
        original_words = set(re.findall(r"\b[a-z]{3,}\b", original.lower()))
        compressed_words = set(re.findall(r"\b[a-z]{3,}\b", compressed.lower()))

        if original_words:
            word_retention = len(original_words & compressed_words) / len(
                original_words
            )
        else:
            word_retention = 1.0

        # Reasoning continuity (presence of logical connectors)
        logical_connectors = [
            "because",
            "therefore",
            "thus",
            "hence",
            "so",
            "if",
            "then",
        ]
        original_logic = sum(
            1 for conn in logical_connectors if conn in original.lower()
        )
        compressed_logic = sum(
            1 for conn in logical_connectors if conn in compressed.lower()
        )

        reasoning_continuity = (
            compressed_logic / original_logic if original_logic > 0 else 1.0
        )

        return SemanticRetentionEvaluation(
            original_entities=original_eval.original_entities,
            compressed_entities=compressed_eval.compressed_entities,
            entity_retention=entity_retention,
            original_topics=original_eval.original_topics,
            compressed_topics=compressed_eval.compressed_topics,
            topic_retention=topic_retention,
            semantic_similarity=word_retention,
            reasoning_continuity_score=min(reasoning_continuity, 1.0),
        )


class TokenBudgetSimulator:
    """Simulates token budgets for different providers."""

    PROVIDER_BUDGETS = {
        ProviderType.CLAUDE: {
            "4k": 4000,
            "8k": 8000,
            "16k": 16000,
            "32k": 32000,
        },
        ProviderType.OPENAI: {
            "4k": 4000,
            "16k": 16000,
            "32k": 32000,
            "128k": 128000,
        },
        ProviderType.GEMINI: {
            "32k": 32000,
            "100k": 100000,
        },
        ProviderType.GENERIC: {
            "4k": 4000,
            "8k": 8000,
            "16k": 16000,
            "32k": 32000,
        },
    }

    @staticmethod
    def get_available_budgets(provider: ProviderType) -> Dict[str, int]:
        """Get available token budgets for provider."""
        return TokenBudgetSimulator.PROVIDER_BUDGETS.get(provider, {})

    @staticmethod
    def calculate_compression_required(
        context_tokens: int, budget: int, reserve: float = 0.2
    ) -> float:
        """
        Calculate compression ratio needed to fit budget.

        Args:
            context_tokens: Original token count
            budget: Target token budget
            reserve: Fraction to reserve for response

        Returns:
            Required compression ratio (0-1)
        """
        available_tokens = int(budget * (1 - reserve))

        if context_tokens <= available_tokens:
            return 0.0  # No compression needed

        required_compression = 1.0 - (available_tokens / context_tokens)
        return min(required_compression, 1.0)
