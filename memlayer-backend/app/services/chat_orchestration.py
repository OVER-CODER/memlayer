"""
Chat orchestration service - Main pipeline for handling user messages.
Coordinates: embedding -> retrieval -> context compilation -> LLM generation -> memory storage

This service remains completely provider-agnostic. It calls the LLM service which
handles all provider-specific logic internally.
"""

from sqlalchemy.orm import Session
from app.db.models import Chat, Message
from app.services.memory_storage import MemoryStorageService
from app.services.memory_retrieval import MemoryRetrievalService
from app.services.context_compilation import ContextCompilationService
from app.services.llm import get_llm_service, LLMService
from app.services.providers import GenerationConfig
from app.core.config import settings
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ChatOrchestrationService:
    """Orchestrates the complete message handling pipeline.

    This service:
    - Remains provider-agnostic
    - Handles the complete message processing pipeline
    - Tracks generation metadata for optimization and debugging
    - Stores all necessary lineage information for memories
    """

    def __init__(self, db: Session, llm_service: LLMService = None):
        """Initialize orchestration service.

        Args:
            db: Database session
            llm_service: Optional LLM service (uses global default if not provided)
        """
        self.db = db
        self.memory_storage = MemoryStorageService(db)
        self.memory_retrieval = MemoryRetrievalService(db)
        self.context_compiler = ContextCompilationService(db)
        self.llm_service = llm_service or get_llm_service()

    def process_message(
        self,
        workspace_id: str,
        chat_id: str,
        query: str,
        top_k_memories: int = None,
        similarity_threshold: float = None,
        provider: str = None,
        model: str = None,
    ) -> dict:
        """
        Process a user message through the complete pipeline.

        Pipeline:
        1. Store user message in memory
        2. Retrieve relevant semantic memories
        3. Compile context
        4. Generate LLM response (with provider switching if specified)
        5. Store response and lineage tracking
        6. Return results with analytics

        Args:
            workspace_id: ID of the workspace
            chat_id: ID of the chat
            query: User message
            top_k_memories: Number of memories to retrieve
            similarity_threshold: Minimum similarity score
            provider: Optional provider to use (switches if different)
            model: Optional model to use

        Returns:
            Dictionary with response and metadata
        """

        # Use defaults from settings if not provided
        top_k_memories = top_k_memories or settings.top_k_memories
        similarity_threshold = (
            similarity_threshold or settings.memory_retrieval_threshold
        )

        # Switch provider if requested
        current_provider = self.llm_service.provider.provider_type.value
        if provider and provider != current_provider:
            logger.info(f"Switching provider from {current_provider} to {provider}")
            self.llm_service.switch_provider(provider, model)

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

        # Store as memory with metadata
        user_memory = self.memory_storage.create_memory(
            workspace_id=workspace_id,
            raw_content=query,
            source_type="user_message",
            importance_score=0.6,
            metadata={"chat_id": chat_id, "message_id": user_message.id},
            generated_from_message_id=user_message.id,
            generated_by_provider=current_provider,
        )

        # Step 2: Retrieve relevant memories
        retrieved_memories, similarity_scores = self.memory_retrieval.retrieve(
            workspace_id=workspace_id,
            query=query,
            top_k=top_k_memories,
            similarity_threshold=similarity_threshold,
        )

        # Track retrieval metadata
        memory_retrieval_record = {
            "workspace_id": workspace_id,
            "query": query,
            "provider_used": current_provider,
            "total_retrieved": len(retrieved_memories),
            "success": True,
            "memory_ids_with_scores": [
                {"id": m.id, "score": s}
                for m, s in zip(retrieved_memories, similarity_scores)
            ],
        }

        # Step 3: Compile context
        context_layers = self.context_compiler.compile_context(
            workspace_id=workspace_id,
            chat_id=chat_id,
            query=query,
            retrieved_memories=retrieved_memories,
            retrieved_scores=similarity_scores,
            provider=current_provider,
            model=self.llm_service.provider.model_name,
            recent_message_count=10,
            max_tokens=2000,
        )

        # Step 4: Generate LLM response with structured config
        generation_result = None
        response_text = None

        try:
            # Create generation config
            gen_config = GenerationConfig(
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                max_tokens=1024,
            )

            # Generate response - provider-agnostic call
            # Use the compiled_prompt from ContextLayers
            generation_result = self.llm_service.generate_with_context(
                context=context_layers.compiled_prompt,
                query=query,
                config=gen_config,
            )

            response_text = generation_result.text

            logger.info(
                f"Generation complete - "
                f"Provider: {generation_result.provider}, "
                f"Model: {generation_result.model}, "
                f"Tokens: {generation_result.tokens_used}, "
                f"Latency: {generation_result.latency_ms}ms"
            )

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            response_text = f"Error generating response: {str(e)}"
            memory_retrieval_record["success"] = False

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

        # Store response as memory with lineage tracking
        response_memory = self.memory_storage.create_memory(
            workspace_id=workspace_id,
            raw_content=response_text,
            source_type="assistant_response",
            importance_score=0.7,
            metadata={
                "chat_id": chat_id,
                "message_id": assistant_message.id,
                "provider": generation_result.provider
                if generation_result
                else current_provider,
                "model": generation_result.model if generation_result else None,
                "tokens_used": generation_result.tokens_used
                if generation_result
                else 0,
                "latency_ms": generation_result.latency_ms if generation_result else 0,
            },
            generated_from_message_id=user_message.id,
            generated_by_provider=generation_result.provider
            if generation_result
            else current_provider,
            # Link to memories that were used to generate this response
            source_memory_ids=[m.id for m in retrieved_memories],
        )

        # Return comprehensive result
        return {
            "message_id": assistant_message.id,
            "response": response_text,
            "provider_used": generation_result.provider
            if generation_result
            else current_provider,
            "model_used": generation_result.model
            if generation_result
            else self.llm_service.provider.model_name,
            "tokens_used": generation_result.tokens_used if generation_result else 0,
            "latency_ms": generation_result.latency_ms if generation_result else 0,
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
            "context_metadata": {
                **context_layers.metadata.dict(),
                "retrieval_stats": memory_retrieval_record,
                "generation_stats": {
                    "tokens_used": generation_result.tokens_used
                    if generation_result
                    else 0,
                    "latency_ms": generation_result.latency_ms
                    if generation_result
                    else 0,
                    "finish_reason": generation_result.metadata.get("finish_reason")
                    if generation_result
                    else None,
                }
                if generation_result
                else {},
            },
            "compiled_context_preview": context_layers.compiled_prompt[:500],
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
