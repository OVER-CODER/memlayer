"""
Semantic Chunking System - Replaces flat memory retrieval with topical structures.

This module implements intelligent semantic chunking to organize memories into
coherent topical groups. Each chunk represents a semantic cluster of related memories
with unified context and compressed representations.

Architecture:
- Topical grouping using hierarchical clustering
- Chunk summaries and centroids
- Token estimation per chunk
- Chunk metadata and lineage tracking
"""

from __future__ import annotations

from typing import List, Dict, Optional, Set, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np
import logging

if TYPE_CHECKING:
    from app.db.models import Memory

logger = logging.getLogger(__name__)


class ChunkType(str, Enum):
    """Types of semantic chunks."""

    CONVERSATION = "conversation"  # Multi-turn conversations
    TOPICAL = "topical"  # Topic-specific memory clusters
    SUMMARY = "summary"  # Pre-summarized information
    WORKSPACE_COGNITION = "workspace_cognition"  # Workspace-specific patterns


@dataclass
class SemanticChunk:
    """Represents a semantic chunk of related memories."""

    chunk_id: str
    chunk_type: ChunkType
    source_memory_ids: List[str] = field(default_factory=list)
    primary_memory: Optional["Memory"] = None

    # Semantic representation
    centroid_embedding: Optional[np.ndarray] = None
    summary: str = ""
    title: str = ""

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    token_estimate: int = 0
    relevance_score: float = 0.0
    cohesion_score: float = 0.0  # How tightly related memories are

    # Tracking
    memory_count: int = 0
    compression_ratio: float = 0.0


@dataclass
class ChunkingMetrics:
    """Metrics for chunking operation."""

    total_memories_input: int = 0
    total_chunks_created: int = 0
    avg_memories_per_chunk: float = 0.0
    avg_chunk_size_tokens: int = 0
    total_tokens_compressed: int = 0
    compression_ratio: float = 0.0
    processing_time_ms: float = 0.0

    # Quality metrics
    avg_cohesion_score: float = 0.0
    chunk_fragmentation: float = 0.0  # % of single-memory chunks


@dataclass
class ChunkingAnalyzer:
    """Analyzes chunking effectiveness and historical trends."""

    @staticmethod
    def analyze_chunking_impact(metrics_list: List[ChunkingMetrics]) -> Dict:
        """Analyze historical chunking performance."""
        if not metrics_list:
            return {}

        return {
            "total_sessions": len(metrics_list),
            "total_memories_processed": sum(
                m.total_memories_input for m in metrics_list
            ),
            "total_chunks_created": sum(m.total_chunks_created for m in metrics_list),
            "avg_compression_ratio": np.mean(
                [m.compression_ratio for m in metrics_list]
            ),
            "avg_cohesion": np.mean([m.avg_cohesion_score for m in metrics_list]),
            "total_time_ms": sum(m.processing_time_ms for m in metrics_list),
        }

    @staticmethod
    def get_chunk_statistics(chunks: List[SemanticChunk]) -> Dict:
        """Get statistics about chunk distribution."""
        if not chunks:
            return {}

        type_counts = {}
        for chunk in chunks:
            chunk_type = chunk.chunk_type.value
            type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1

        memory_counts = [len(chunk.source_memory_ids) for chunk in chunks]

        return {
            "total_chunks": len(chunks),
            "type_distribution": type_counts,
            "avg_memories_per_chunk": np.mean(memory_counts) if memory_counts else 0,
            "max_memories_in_chunk": max(memory_counts) if memory_counts else 0,
            "min_memories_in_chunk": min(memory_counts) if memory_counts else 0,
            "total_memories_tracked": sum(memory_counts),
        }


class SemanticChunkingService:
    """Service for semantic chunking of memories."""

    def __init__(
        self,
        embedding_service=None,
        min_chunk_size: int = 2,
        max_chunk_size: int = 10,
        similarity_threshold: float = 0.70,
    ):
        """
        Initialize chunking service.

        Args:
            embedding_service: Service for generating embeddings
            min_chunk_size: Minimum memories per chunk
            max_chunk_size: Maximum memories per chunk
            similarity_threshold: Threshold for grouping memories
        """
        # Lazy load embedding service to avoid circular imports
        if embedding_service is None:
            try:
                from app.services.embedding import get_embedding_service

                self.embedding_service = get_embedding_service()
            except ImportError:
                self.embedding_service = None
        else:
            self.embedding_service = embedding_service

        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.similarity_threshold = similarity_threshold

    def chunk_memories(
        self,
        memories: List["Memory"],
        chunk_type: ChunkType = ChunkType.TOPICAL,
    ) -> Tuple[List[SemanticChunk], ChunkingMetrics]:
        """
        Create semantic chunks from memories.

        Args:
            memories: List of memories to chunk
            chunk_type: Type of chunks to create

        Returns:
            Tuple of (chunks, metrics)
        """
        import time

        start_time = time.time()

        if not memories:
            return [], ChunkingMetrics()

        # Step 1: Build similarity matrix
        embeddings = self._precompute_embeddings(memories)
        similarity_matrix = self._build_similarity_matrix(embeddings, memories)

        # Step 2: Find topical groups using hierarchical grouping
        groups = self._find_topical_groups(memories, similarity_matrix)

        # Step 3: Create chunks from groups
        chunks = self._create_chunks_from_groups(memories, groups, chunk_type)

        # Step 4: Generate chunk summaries and centroids
        for chunk in chunks:
            self._enrich_chunk(chunk, memories)

        # Step 5: Calculate metrics
        metrics = self._calculate_metrics(memories, chunks, time.time() - start_time)

        logger.info(
            f"Chunking complete: {len(memories)} → {len(chunks)} chunks, "
            f"compression ratio: {metrics.compression_ratio:.2f}"
        )

        return chunks, metrics

    def _precompute_embeddings(self, memories: List["Memory"]) -> Dict[str, np.ndarray]:
        """Precompute and normalize embeddings for all memories."""
        embeddings = {}
        for memory in memories:
            if memory.embedding is not None:
                emb = np.array(memory.embedding)
                # Normalize
                norm = np.linalg.norm(emb)
                if norm > 0:
                    emb = emb / norm
                embeddings[memory.id] = emb

        return embeddings

    def _build_similarity_matrix(
        self,
        embeddings: Dict[str, np.ndarray],
        memories: List["Memory"],
    ) -> Dict[Tuple[str, str], float]:
        """Build pairwise similarity matrix using cosine distance."""
        similarity_matrix = {}

        memory_ids = [m.id for m in memories]
        for i, mem1_id in enumerate(memory_ids):
            if mem1_id not in embeddings:
                continue

            for mem2_id in memory_ids[i + 1 :]:
                if mem2_id not in embeddings:
                    continue

                # Cosine similarity
                sim = float(np.dot(embeddings[mem1_id], embeddings[mem2_id]))
                key = (mem1_id, mem2_id)
                similarity_matrix[key] = sim

        return similarity_matrix

    def _find_topical_groups(
        self,
        memories: List["Memory"],
        similarity_matrix: Dict[Tuple[str, str], float],
    ) -> List[List[str]]:
        """Find topical groups using hierarchical clustering."""
        if not memories:
            return []

        # Simple greedy clustering based on similarity
        memory_ids = [m.id for m in memories]
        assigned = set()
        groups = []

        for mem_id in memory_ids:
            if mem_id in assigned:
                continue

            # Start new group
            group = [mem_id]
            assigned.add(mem_id)

            # Add similar memories to this group
            for other_id in memory_ids:
                if other_id in assigned or len(group) >= self.max_chunk_size:
                    continue

                # Check similarity
                key = (
                    (mem_id, other_id)
                    if (mem_id, other_id) in similarity_matrix
                    else (other_id, mem_id)
                )
                if key in similarity_matrix:
                    if similarity_matrix[key] >= self.similarity_threshold:
                        group.append(other_id)
                        assigned.add(other_id)

            # Always add groups, even single memories
            groups.append(group)

        return groups

    def _create_chunks_from_groups(
        self,
        memories: List["Memory"],
        groups: List[List[str]],
        chunk_type: ChunkType,
    ) -> List[SemanticChunk]:
        """Create SemanticChunk objects from memory groups."""
        memory_by_id = {m.id: m for m in memories}
        chunks = []

        for i, group in enumerate(groups):
            chunk_id = f"chunk_{chunk_type.value}_{i}_{int(datetime.utcnow().timestamp() * 1000)}"

            chunk = SemanticChunk(
                chunk_id=chunk_id,
                chunk_type=chunk_type,
                source_memory_ids=group,
                memory_count=len(group),
            )

            # Set primary memory (first or most important)
            if group and group[0] in memory_by_id:
                chunk.primary_memory = memory_by_id[group[0]]

            chunks.append(chunk)

        return chunks

    def _enrich_chunk(self, chunk: SemanticChunk, all_memories: List["Memory"]) -> None:
        """Enrich chunk with summary, centroid, and metadata."""
        memory_by_id = {m.id: m for m in all_memories}
        memories_in_chunk = [
            memory_by_id[mid] for mid in chunk.source_memory_ids if mid in memory_by_id
        ]

        if not memories_in_chunk:
            return

        # Generate chunk title
        if chunk.primary_memory:
            chunk.title = (
                f"{chunk.chunk_type.value}: {chunk.primary_memory.raw_content[:50]}"
            )

        # Estimate tokens
        total_content = " ".join([m.raw_content for m in memories_in_chunk])
        chunk.token_estimate = len(total_content) // 4  # Rough estimate

        # Generate summary (simple: concatenate first 100 chars of each)
        summaries = [m.raw_content[:50] for m in memories_in_chunk[:3]]
        chunk.summary = " | ".join(summaries)

        # Calculate centroid embedding
        embeddings_in_chunk = [
            np.array(m.embedding) for m in memories_in_chunk if m.embedding is not None
        ]
        if embeddings_in_chunk:
            chunk.centroid_embedding = np.mean(embeddings_in_chunk, axis=0)
            # Normalize centroid
            norm = np.linalg.norm(chunk.centroid_embedding)
            if norm > 0:
                chunk.centroid_embedding = chunk.centroid_embedding / norm

        # Calculate cohesion (average similarity within chunk)
        if len(embeddings_in_chunk) > 1:
            similarities = []
            for i in range(len(embeddings_in_chunk)):
                for j in range(i + 1, len(embeddings_in_chunk)):
                    sim = float(np.dot(embeddings_in_chunk[i], embeddings_in_chunk[j]))
                    similarities.append(sim)
            chunk.cohesion_score = float(np.mean(similarities)) if similarities else 0.0
        else:
            chunk.cohesion_score = 1.0

    def _calculate_metrics(
        self,
        memories: List["Memory"],
        chunks: List[SemanticChunk],
        processing_time_ms: float,
    ) -> ChunkingMetrics:
        """Calculate comprehensive chunking metrics."""
        total_original_tokens = sum(len(m.raw_content) // 4 for m in memories)
        total_chunk_tokens = sum(chunk.token_estimate for chunk in chunks)

        single_memory_chunks = sum(
            1 for chunk in chunks if len(chunk.source_memory_ids) == 1
        )

        metrics = ChunkingMetrics(
            total_memories_input=len(memories),
            total_chunks_created=len(chunks),
            avg_memories_per_chunk=(len(memories) / len(chunks) if chunks else 0),
            avg_chunk_size_tokens=(total_chunk_tokens // len(chunks) if chunks else 0),
            total_tokens_compressed=max(0, total_original_tokens - total_chunk_tokens),
            compression_ratio=(
                (total_original_tokens - total_chunk_tokens) / total_original_tokens
                if total_original_tokens > 0
                else 0.0
            ),
            processing_time_ms=processing_time_ms * 1000,
            avg_cohesion_score=np.mean([c.cohesion_score for c in chunks])
            if chunks
            else 0.0,
            chunk_fragmentation=(
                (single_memory_chunks / len(chunks) * 100) if chunks else 0.0
            ),
        )

        return metrics
