"""
Memory retrieval service using semantic search with pgvector.
Deterministic ranking: similarity DESC, importance DESC, timestamp ASC, id ASC
"""

from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.models import Memory, MemoryRetrieval
from app.services.embedding import get_embedding_service
from app.embeddings import get_embedding_factory
from typing import List, Tuple, Optional
import uuid
from datetime import datetime, timezone


class MemoryRetrievalService:
    """Retrieves semantically relevant memories from the vector store."""

    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = get_embedding_service()
        self.embedding_factory = get_embedding_factory()

    def retrieve(
        self,
        workspace_id: str,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.3,
    ) -> Tuple[List[Memory], List[float]]:
        """
        Retrieve semantically similar memories for a query.
        Uses vector similarity when embeddings are available, falls back to text matching.

        DETERMINISTIC RANKING ORDER:
        1. similarity_score DESC
        2. importance_score DESC
        3. timestamp ASC
        4. memory_id ASC

        This ordering MUST NEVER vary for identical inputs.

        Args:
            workspace_id: ID of the workspace
            query: Query text
            top_k: Number of memories to retrieve
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            Tuple of (memories, similarity_scores)
        """
        # Try to generate embedding using factory
        query_embedding = None
        try:
            factory = get_embedding_factory()
            query_embedding = factory.embed_text(query)
        except Exception:
            pass

        # Fallback to legacy service
        if query_embedding is None:
            try:
                query_embedding = self.embedding_service.embed(query)
            except Exception:
                pass

        # Check if we have valid embeddings in the database
        memories_with_embeddings = (
            self.db.query(Memory)
            .filter(Memory.workspace_id == workspace_id)
            .filter(Memory.embedding.isnot(None))
            .limit(100)
            .all()
        )

        # If we have embeddings and a query embedding, use vector similarity
        if query_embedding and memories_with_embeddings:
            try:
                # Use pgvector cosine similarity (<=> operator)
                # Apply deterministic ordering: similarity DESC, importance DESC, timestamp ASC, id ASC
                results = (
                    self.db.query(
                        Memory,
                        (
                            1
                            - func.cast(
                                Memory.embedding.op("<=>")(query_embedding), float
                            )
                        ).label("similarity"),
                    )
                    .filter(Memory.workspace_id == workspace_id)
                    .filter(Memory.embedding.isnot(None))
                    .filter(
                        1
                        - func.cast(Memory.embedding.op("<=>")(query_embedding), float)
                        >= similarity_threshold
                    )
                    .order_by(
                        func.cast(
                            Memory.embedding.op("<=>")(query_embedding), float
                        ).asc(),  # similarity DESC (1-similarity = distance)
                        Memory.importance_score.desc(),  # importance DESC
                        Memory.timestamp.asc(),  # timestamp ASC
                        Memory.id.asc(),  # memory_id ASC (deterministic tiebreaker)
                    )
                    .limit(top_k)
                    .all()
                )

                similarities = [1.0 - float(r[1]) for r in results]
                return [r[0] for r in results], similarities
            except Exception:
                # Vector query failed, fall back to text matching
                pass

        # Fallback: text-based matching with deterministic ordering
        memories = (
            self.db.query(Memory)
            .filter(Memory.workspace_id == workspace_id)
            .order_by(
                Memory.importance_score.desc(),
                Memory.timestamp.asc(),
                Memory.id.asc(),
            )
            .limit(top_k * 3)
            .all()
        )

        results = []
        query_lower = query.lower()

        for mem in memories:
            content = (mem.raw_content or "").lower()
            summary = (mem.summary or "").lower()

            query_words = set(query_lower.split())
            content_words = set(content.split())
            summary_words = set(summary.split())

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
                # Apply importance weighting
                weighted_score = (score * 0.7) + (mem.importance_score * 0.3)
                results.append((mem, weighted_score))

        # Deterministic sort: score DESC, timestamp ASC, id ASC
        results.sort(key=lambda x: (-x[1], x[0].timestamp, x[0].id))
        results = results[:top_k]

        return [r[0] for r in results], [r[1] for r in results]

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
