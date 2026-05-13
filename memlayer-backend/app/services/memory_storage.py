"""
Memory storage service for saving and managing semantic memories.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models import Memory, Workspace
from app.services.embedding import get_embedding_service
from app.schemas.memory import MemoryCreate, MemoryResponse
from typing import List, Optional
import uuid
from datetime import datetime, timezone


class MemoryStorageService:
    """Manages semantic memory storage and retrieval."""

    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = get_embedding_service()

    def create_memory(
        self,
        workspace_id: str,
        raw_content: str,
        source_type: str = "user_message",
        summary: Optional[str] = None,
        importance_score: float = 0.5,
        metadata: Optional[dict] = None,
        generated_from_message_id: Optional[str] = None,
        generated_by_provider: Optional[str] = None,
        source_memory_ids: Optional[List[str]] = None,
    ) -> Memory:
        """Create and store a new semantic memory with lineage tracking.

        Args:
            workspace_id: Workspace this memory belongs to
            raw_content: Raw content to be remembered
            source_type: Type of source (user_message, assistant_response, etc)
            summary: Optional summary (auto-generated if not provided)
            importance_score: Importance score (0-1)
            metadata: Additional metadata
            generated_from_message_id: ID of the message that generated this memory
            generated_by_provider: Provider that generated this memory
            source_memory_ids: IDs of memories that were used to create this

        Returns:
            Created Memory object
        """
        # Generate embedding
        embedding = None
        try:
            embedding = self.embedding_service.embed(raw_content)
        except Exception:
            # Embedding generation failed - continue without
            pass

        # Create memory object with lineage tracking
        memory = Memory(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            source_type=source_type,
            raw_content=raw_content,
            summary=summary or raw_content[:200],
            embedding=embedding,
            importance_score=importance_score,
            extra_metadata=metadata or {},
            timestamp=datetime.now(timezone.utc),
            generated_from_message_id=generated_from_message_id,
            generated_by_provider=generated_by_provider,
            source_memory_ids=source_memory_ids or [],
        )

        # Save to database
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)

        return memory

    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Retrieve a memory by ID."""
        return self.db.query(Memory).filter(Memory.id == memory_id).first()

    def list_workspace_memories(
        self,
        workspace_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Memory]:
        """List all memories for a workspace."""
        return (
            self.db.query(Memory)
            .filter(Memory.workspace_id == workspace_id)
            .order_by(desc(Memory.timestamp))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory."""
        memory = self.get_memory(memory_id)
        if memory:
            self.db.delete(memory)
            self.db.commit()
            return True
        return False

    def update_importance(
        self, memory_id: str, importance_score: float
    ) -> Optional[Memory]:
        """Update importance score of a memory."""
        memory = self.get_memory(memory_id)
        if memory:
            memory.importance_score = importance_score
            self.db.commit()
            self.db.refresh(memory)
        return memory

    def get_memory_stats(self, workspace_id: str) -> dict:
        """Get statistics about memories in a workspace."""
        memories = (
            self.db.query(Memory).filter(Memory.workspace_id == workspace_id).all()
        )

        return {
            "total_memories": len(memories),
            "by_source": self._count_by_source(memories),
            "avg_importance": sum(m.importance_score for m in memories) / len(memories)
            if memories
            else 0,
            "oldest_memory": min((m.timestamp for m in memories), default=None),
            "newest_memory": max((m.timestamp for m in memories), default=None),
        }

    def _count_by_source(self, memories: List[Memory]) -> dict:
        """Count memories by source type."""
        counts = {}
        for memory in memories:
            counts[memory.source_type] = counts.get(memory.source_type, 0) + 1
        return counts
