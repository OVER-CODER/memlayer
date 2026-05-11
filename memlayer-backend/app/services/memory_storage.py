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
from datetime import datetime


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
    ) -> Memory:
        """Create and store a new semantic memory."""

        # Generate embedding
        embedding = self.embedding_service.embed(raw_content)

        # Create memory object
        memory = Memory(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            source_type=source_type,
            raw_content=raw_content,
            summary=summary or raw_content[:200],
            embedding=embedding,
            importance_score=importance_score,
            metadata=metadata or {},
            timestamp=datetime.utcnow(),
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
