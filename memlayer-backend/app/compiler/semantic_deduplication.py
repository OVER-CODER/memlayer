"""
Semantic Deduplication Engine - Identifies and merges redundant memories.

This module implements intelligent deduplication strategies to eliminate
redundant context before compilation. Core to context optimization.

Architecture:
- Overlap detection using semantic similarity
- Redundancy scoring
- Configurable merge strategies
- Metrics tracking for optimization analysis
"""

from __future__ import annotations

from typing import List, Tuple, Dict, Optional, Set, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime, timezone
import numpy as np
from enum import Enum
import logging

if TYPE_CHECKING:
    from app.db.models import Memory

logger = logging.getLogger(__name__)


class MergeStrategy(str, Enum):
    """Strategies for handling redundant memories."""

    KEEP_HIGHEST_IMPORTANCE = "keep_highest_importance"  # Keep most important
    KEEP_MOST_RECENT = "keep_most_recent"  # Keep newest
    KEEP_LONGEST = "keep_longest"  # Keep with most content
    MERGE_SUMMARIES = "merge_summaries"  # Combine into summary


@dataclass
class DuplicateGroup:
    """Represents a group of duplicate/near-duplicate memories."""

    primary_memory: "Memory"  # Using string annotation for forward reference
    redundant_memories: List["Memory"] = field(default_factory=list)
    overlap_score: float = 0.0
    token_savings: int = 0
    merge_strategy: MergeStrategy = MergeStrategy.KEEP_HIGHEST_IMPORTANCE


@dataclass
class DeduplicationMetrics:
    """Metrics tracking deduplication effectiveness."""

    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_memories_input: int = 0
    total_memories_after: int = 0
    duplicate_groups_found: int = 0
    duplicates_removed: int = 0
    token_savings: int = 0
    compression_ratio: float = 0.0
    processing_time_ms: float = 0.0

    def __post_init__(self):
        if self.total_memories_input > 0:
            self.compression_ratio = (
                self.token_savings / self.total_memories_input * 100
            )


class SemanticDeduplicationService:
    """Deduplicates redundant memories based on semantic overlap.

    This service identifies memories that convey similar information
    and removes or merges them, reducing redundant context while
    preserving semantic information.

    Principles:
    - Deterministic (same input = same output)
    - Measurable (track all optimizations)
    - Configurable (adjustable thresholds)
    - Reversible (log what was removed)
    """

    def __init__(self, embedding_service=None):
        # Lazy load embedding service to avoid circular imports
        if embedding_service is None:
            try:
                from app.services.embedding import get_embedding_service

                self.embedding_service = get_embedding_service()
            except ImportError:
                self.embedding_service = None
        else:
            self.embedding_service = embedding_service

        # Overlap threshold: memories more similar than this are considered duplicates
        self.overlap_threshold = 0.85
        # Minimum overlap to consider for deduplication
        self.min_overlap_for_consideration = 0.7
        # Importance threshold: if one memory is much more important, prefer it
        self.importance_threshold = 0.3

    def deduplicate(
        self,
        memories: List["Memory"],
        strategy: MergeStrategy = MergeStrategy.KEEP_HIGHEST_IMPORTANCE,
        overlap_threshold: Optional[float] = None,
    ) -> Tuple[List["Memory"], DeduplicationMetrics, List[DuplicateGroup]]:
        """
        Deduplicate a list of memories.

        Args:
            memories: List of memories to deduplicate
            strategy: How to handle redundant memories
            overlap_threshold: Override default threshold

        Returns:
            Tuple of (deduplicated_memories, metrics, duplicate_groups)
        """
        import time

        start_time = time.time()

        if overlap_threshold:
            self.overlap_threshold = overlap_threshold

        # Find all duplicate groups
        duplicate_groups = self._find_duplicate_groups(memories)

        # Select which memory IDs to keep
        kept_ids = self._select_memories_to_keep(duplicate_groups, strategy)

        # Include all non-duplicated memories
        all_duplicate_ids = {group.primary_memory.id for group in duplicate_groups}
        all_duplicate_ids.update(
            m.id for group in duplicate_groups for m in group.redundant_memories
        )
        non_duplicate_ids = {m.id for m in memories if m.id not in all_duplicate_ids}
        kept_ids.update(non_duplicate_ids)

        # Filter memories to keep
        memories_to_keep = [m for m in memories if m.id in kept_ids]

        # Create memory of what was removed
        memories_removed = [m for m in memories if m.id not in kept_ids]

        # Calculate metrics
        token_savings = sum(len(m.raw_content) // 4 for m in memories_removed)

        metrics = DeduplicationMetrics(
            total_memories_input=len(memories),
            total_memories_after=len(memories_to_keep),
            duplicate_groups_found=len(duplicate_groups),
            duplicates_removed=len(memories_removed),
            token_savings=token_savings,
            processing_time_ms=(time.time() - start_time) * 1000,
        )

        logger.info(
            f"Deduplication complete: "
            f"{len(memories)} → {len(memories_to_keep)} memories, "
            f"{token_savings} token savings, "
            f"{len(duplicate_groups)} groups"
        )

        return memories_to_keep, metrics, duplicate_groups

    def _find_duplicate_groups(self, memories: List["Memory"]) -> List[DuplicateGroup]:
        """Find groups of semantically similar memories.

        Uses pairwise semantic similarity to identify overlapping memories.
        """
        if not memories:
            return []

        groups: List[DuplicateGroup] = []
        processed_ids: Set[str] = set()

        # Precompute embeddings for efficiency
        embeddings = {}
        for memory in memories:
            if memory.embedding is not None:
                embeddings[memory.id] = np.array(memory.embedding)

        # Find duplicate groups
        for i, memory1 in enumerate(memories):
            if memory1.id in processed_ids:
                continue

            if memory1.id not in embeddings:
                continue

            duplicates = []

            # Compare against all subsequent memories
            for memory2 in memories[i + 1 :]:
                if memory2.id in processed_ids:
                    continue
                if memory2.id not in embeddings:
                    continue

                # Calculate semantic overlap
                overlap = self._calculate_overlap(
                    embeddings[memory1.id], embeddings[memory2.id]
                )

                if overlap >= self.overlap_threshold:
                    duplicates.append(memory2)
                    processed_ids.add(memory2.id)

            # If we found duplicates, create a group
            if duplicates:
                group = DuplicateGroup(
                    primary_memory=memory1,
                    redundant_memories=duplicates,
                    overlap_score=overlap,
                )
                groups.append(group)
                processed_ids.add(memory1.id)

        return groups

    def _calculate_overlap(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
    ) -> float:
        """Calculate semantic overlap between two embeddings.

        Uses cosine similarity: values from 0 (orthogonal) to 1 (identical).
        """
        # Normalize embeddings
        e1 = embedding1 / (np.linalg.norm(embedding1) + 1e-8)
        e2 = embedding2 / (np.linalg.norm(embedding2) + 1e-8)

        # Cosine similarity
        similarity = np.dot(e1, e2)

        # Return as 0-1 range
        return float(max(0.0, min(1.0, (similarity + 1) / 2)))

    def _select_memories_to_keep(
        self,
        duplicate_groups: List[DuplicateGroup],
        strategy: MergeStrategy,
    ) -> Set[str]:
        """Select which memories to keep from each duplicate group."""

        kept = set()

        # For each group, select primary based on strategy
        for group in duplicate_groups:
            if strategy == MergeStrategy.KEEP_HIGHEST_IMPORTANCE:
                primary = self._select_by_importance(
                    [group.primary_memory] + group.redundant_memories
                )
            elif strategy == MergeStrategy.KEEP_MOST_RECENT:
                primary = self._select_by_recency(
                    [group.primary_memory] + group.redundant_memories
                )
            elif strategy == MergeStrategy.KEEP_LONGEST:
                primary = self._select_by_length(
                    [group.primary_memory] + group.redundant_memories
                )
            else:
                primary = group.primary_memory

            kept.add(primary.id)

        # Add all non-duplicated memories
        all_ids = {group.primary_memory.id for group in duplicate_groups}
        all_ids.update(
            m.id for group in duplicate_groups for m in group.redundant_memories
        )

        return kept

    def _select_by_importance(self, memories: list[Memory]) -> Memory:
        """Select memory with highest importance score."""
        return max(memories, key=lambda m: m.importance_score)

    def _select_by_recency(self, memories: list[Memory]) -> Memory:
        """Select most recent memory."""
        return max(memories, key=lambda m: m.timestamp)

    def _select_by_length(self, memories: list[Memory]) -> Memory:
        """Select memory with most content."""
        return max(memories, key=lambda m: len(m.raw_content))


class DeduplicationAnalyzer:
    """Analyzes deduplication effectiveness and provides insights."""

    @staticmethod
    def analyze_deduplication_impact(
        metrics_history: List[DeduplicationMetrics],
    ) -> Dict:
        """Analyze effectiveness of deduplication over time."""

        if not metrics_history:
            return {}

        return {
            "total_sessions": len(metrics_history),
            "avg_token_savings": sum(m.token_savings for m in metrics_history)
            / len(metrics_history),
            "total_token_savings": sum(m.token_savings for m in metrics_history),
            "avg_compression_ratio": sum(m.compression_ratio for m in metrics_history)
            / len(metrics_history),
            "avg_duplicates_found": sum(
                m.duplicate_groups_found for m in metrics_history
            )
            / len(metrics_history),
            "avg_processing_time_ms": sum(m.processing_time_ms for m in metrics_history)
            / len(metrics_history),
        }

    @staticmethod
    def get_duplicate_statistics(groups: List[DuplicateGroup]) -> Dict:
        """Get statistics about duplicate groups."""

        if not groups:
            return {"duplicate_groups": 0}

        group_sizes = [len(g.redundant_memories) + 1 for g in groups]

        return {
            "duplicate_groups": len(groups),
            "total_duplicates": sum(len(g.redundant_memories) for g in groups),
            "avg_group_size": sum(group_sizes) / len(group_sizes),
            "max_group_size": max(group_sizes),
            "avg_overlap_score": sum(g.overlap_score for g in groups) / len(groups),
        }
