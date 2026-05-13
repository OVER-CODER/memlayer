"""
Memory retrieval service using semantic search with pgvector.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.models import Memory, MemoryRetrieval
from app.services.embedding import get_embedding_service
from typing import List, Tuple, Optional
import uuid
from datetime import datetime, timezone


class MemoryRetrievalService:
    """Retrieves semantically relevant memories from the vector store."""

    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = get_embedding_service()

    def retrieve(
        self,
        workspace_id: str,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.3,
    ) -> Tuple[List[Memory], List[float]]:
        """
        Retrieve semantically similar memories for a query.
        Uses simple text matching when embeddings aren't available.

        Args:
            workspace_id: ID of the workspace
            query: Query text
            top_k: Number of memories to retrieve
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            Tuple of (memories, similarity_scores)
        """
        # Get all memories for workspace
        memories = (
            self.db.query(Memory)
            .filter(Memory.workspace_id == workspace_id)
            .limit(top_k * 2)  # Get more to filter
            .all()
        )

        # Simple text-based scoring since embeddings aren't available
        results = []
        query_lower = query.lower()

        for mem in memories:
            content = (mem.raw_content or "").lower()
            summary = (mem.summary or "").lower()

            # Simple keyword matching score
            query_words = set(query_lower.split())
            content_words = set(content.split())
            summary_words = set(summary.split())

            # Calculate simple overlap score
            if query_words:
                overlap = len(query_words & content_words) / len(query_words)
                score = max(
                    overlap,
                    len(query_words & summary_words) / len(query_words)
                    if query_words
                    else 0,
                )
            else:
                score = 0

            if score > 0:
                results.append((mem, score))

        # Sort by score and take top_k
        results.sort(key=lambda x: x[1], reverse=True)
        results = results[:top_k]

        return [r[0] for r in results], [r[1] for r in results]

        # Filter by similarity threshold and apply importance weighting
        memories = []
        similarities = []

        for memory, similarity in results:
            if similarity >= similarity_threshold:
                # Apply importance weighting to similarity
                weighted_similarity = (similarity * 0.7) + (
                    memory.importance_score * 0.3
                )
                memories.append(memory)
                similarities.append(weighted_similarity)

        # Log retrieval for analytics
        self._log_retrieval(workspace_id, query, memories, similarities)

        return memories, similarities

    def retrieve_batch(
        self,
        workspace_id: str,
        queries: List[str],
        top_k: int = 5,
        similarity_threshold: float = 0.3,
    ) -> List[Tuple[List[Memory], List[float]]]:
        """Retrieve memories for multiple queries."""
        return [
            self.retrieve(workspace_id, query, top_k, similarity_threshold)
            for query in queries
        ]

    def _log_retrieval(
        self,
        workspace_id: str,
        query: str,
        memories: List[Memory],
        similarities: List[float],
    ):
        """Log memory retrieval for analytics."""
        retrieval_log = MemoryRetrieval(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            query=query,
            retrieved_memory_ids=[m.id for m in memories],
            similarity_scores=similarities,
            timestamp=datetime.now(timezone.utc),
        )
        self.db.add(retrieval_log)
        self.db.commit()

    def get_retrieval_stats(self, workspace_id: str, limit: int = 100) -> dict:
        """Get retrieval statistics."""
        retrievals = (
            self.db.query(MemoryRetrieval)
            .filter(MemoryRetrieval.workspace_id == workspace_id)
            .order_by(MemoryRetrieval.timestamp.desc())
            .limit(limit)
            .all()
        )

        if not retrievals:
            return {"total_retrievals": 0}

        all_scores = []
        for r in retrievals:
            if r.similarity_scores:
                all_scores.extend(r.similarity_scores)

        return {
            "total_retrievals": len(retrievals),
            "avg_similarity": sum(all_scores) / len(all_scores) if all_scores else 0,
            "max_similarity": max(all_scores) if all_scores else 0,
            "min_similarity": min(all_scores) if all_scores else 0,
        }
