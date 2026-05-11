"""
Chat orchestration service - Main pipeline for handling user messages.
Coordinates: embedding -> retrieval -> context compilation -> LLM generation -> memory storage
"""

from sqlalchemy.orm import Session
from app.db.models import Chat, Message
from app.services.memory_storage import MemoryStorageService
from app.services.memory_retrieval import MemoryRetrievalService
from app.services.context_compilation import ContextCompilationService
from app.services.llm import get_llm_service
from app.core.config import settings
import uuid
from datetime import datetime


class ChatOrchestrationService:
    """Orchestrates the complete message handling pipeline."""

    def __init__(self, db: Session):
        self.db = db
        self.memory_storage = MemoryStorageService(db)
        self.memory_retrieval = MemoryRetrievalService(db)
        self.context_compiler = ContextCompilationService(db)
        self.llm_service = get_llm_service()

    def process_message(
        self,
        workspace_id: str,
        chat_id: str,
        query: str,
        top_k_memories: int = None,
        similarity_threshold: float = None,
    ) -> dict:
        """
        Process a user message through the complete pipeline.

        Pipeline:
        1. Store user message in memory
        2. Retrieve relevant semantic memories
        3. Compile context
        4. Generate LLM response
        5. Store response in memory
        6. Return results with analytics
        """

        # Use defaults from settings if not provided
        top_k_memories = top_k_memories or settings.top_k_memories
        similarity_threshold = (
            similarity_threshold or settings.memory_retrieval_threshold
        )

        # Step 1: Store user message
        user_message = Message(
            id=str(uuid.uuid4()),
            chat_id=chat_id,
            role="user",
            content=query,
            created_at=datetime.utcnow(),
        )
        self.db.add(user_message)
        self.db.commit()
        self.db.refresh(user_message)

        # Store as memory
        self.memory_storage.create_memory(
            workspace_id=workspace_id,
            raw_content=query,
            source_type="user_message",
            importance_score=0.6,
            metadata={"chat_id": chat_id, "message_id": user_message.id},
        )

        # Step 2: Retrieve relevant memories
        retrieved_memories, similarity_scores = self.memory_retrieval.retrieve(
            workspace_id=workspace_id,
            query=query,
            top_k=top_k_memories,
            similarity_threshold=similarity_threshold,
        )

        # Step 3: Compile context
        context_data = self.context_compiler.compile_context(
            workspace_id=workspace_id,
            chat_id=chat_id,
            query=query,
            retrieved_memories=retrieved_memories,
            retrieved_scores=similarity_scores,
            recent_message_count=10,
            max_tokens=2000,
        )

        # Step 4: Generate LLM response
        try:
            response_text = self.llm_service.generate_with_context(
                context=context_data["compiled_prompt"],
                query=query,
                temperature=0.7,
                max_tokens=1024,
            )
        except Exception as e:
            response_text = f"Error generating response: {str(e)}"

        # Step 5: Store response and extracted memories
        assistant_message = Message(
            id=str(uuid.uuid4()),
            chat_id=chat_id,
            role="assistant",
            content=response_text,
            created_at=datetime.utcnow(),
        )
        self.db.add(assistant_message)
        self.db.commit()
        self.db.refresh(assistant_message)

        # Store response as memory
        self.memory_storage.create_memory(
            workspace_id=workspace_id,
            raw_content=response_text,
            source_type="assistant_response",
            importance_score=0.7,
            metadata={"chat_id": chat_id, "message_id": assistant_message.id},
        )

        # Return comprehensive result
        return {
            "message_id": assistant_message.id,
            "response": response_text,
            "retrieved_memories": [
                {
                    "id": m.id,
                    "content": m.raw_content[:500],
                    "summary": m.summary,
                    "source_type": m.source_type,
                    "similarity_score": s,
                    "importance_score": m.importance_score,
                    "timestamp": m.timestamp.isoformat(),
                }
                for m, s in zip(retrieved_memories, similarity_scores)
            ],
            "context_metadata": context_data["metadata"],
            "compiled_context_preview": context_data["compiled_prompt"][:500],
        }

    def get_chat_messages(self, chat_id: str, limit: int = 50) -> list:
        """Get chat messages in chronological order."""
        chat = self.db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            return []

        messages = (
            self.db.query(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(Message.created_at)
            .limit(limit)
            .all()
        )

        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "timestamp": m.created_at.isoformat(),
            }
            for m in messages
        ]
