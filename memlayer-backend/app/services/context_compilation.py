"""
Context compilation service that assembles structured context from memories.

This service creates ContextLayers objects that represent context
in distinct, composable layers that providers can format as needed.
"""

from typing import List, Optional
from app.db.models import Memory, Message, Workspace
from app.schemas.context import (
    ContextLayers,
    CompilationMetadata,
    CompilationStrategy,
    ChatHistoryLayer,
    MemoryLayer,
    WorkspaceSummaryLayer,
)
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import logging
import time

logger = logging.getLogger(__name__)


class ContextCompilationService:
    """Assembles structured context from memories and recent chat history.

    This service creates ContextLayers objects with:
    - Distinct context layers (chat history, memories, workspace summary)
    - Compilation metadata for debugging and optimization
    - Provider-agnostic representation
    """

    def __init__(self, db: Session):
        self.db = db

    def compile_context(
        self,
        workspace_id: str,
        chat_id: str,
        query: str,
        retrieved_memories: List[Memory],
        retrieved_scores: List[float],
        provider: str = "gemini",
        model: str = "gemini-pro",
        recent_message_count: int = 10,
        max_tokens: int = 2000,
        compilation_strategy: CompilationStrategy = CompilationStrategy.FULL_CONTEXT,
    ) -> ContextLayers:
        """
        Compile a structured context for the LLM.

        Args:
            workspace_id: ID of the workspace
            chat_id: ID of the chat
            query: User query
            retrieved_memories: List of retrieved Memory objects
            retrieved_scores: Similarity scores for memories
            provider: Provider name
            model: Model name
            recent_message_count: Number of recent messages to include
            max_tokens: Maximum tokens for context
            compilation_strategy: Strategy for compilation

        Returns:
            ContextLayers object with structured context
        """
        compilation_start = time.time()

        # Get recent chat messages
        recent_messages = self._get_recent_messages(chat_id, recent_message_count)

        # Build chat history layer
        chat_history_layer = self._build_chat_history_layer(recent_messages)

        # Build semantic memories layer
        memory_layers = self._build_memory_layers(
            retrieved_memories, retrieved_scores, compilation_strategy
        )

        # Build workspace summary layer
        workspace_summary_layer = self._build_workspace_summary_layer(workspace_id)

        # Estimate tokens
        token_estimate = self._estimate_total_tokens(
            chat_history_layer, memory_layers, workspace_summary_layer, query
        )

        # Create metadata
        compilation_time_ms = (time.time() - compilation_start) * 1000
        metadata = CompilationMetadata(
            provider=provider,
            model=model,
            compilation_strategy=compilation_strategy,
            token_estimate=token_estimate,
            token_limit=max_tokens,
            retrieved_memory_ids=[m.id for m in retrieved_memories],
            retrieved_scores=list(retrieved_scores),
            compilation_time_ms=compilation_time_ms,
        )

        # Create structured context
        context = ContextLayers(
            chat_history=chat_history_layer,
            semantic_memories=memory_layers,
            workspace_summary=workspace_summary_layer,
            metadata=metadata,
            compiled_prompt="",  # Will be set after formatting by provider
        )

        # Build and attach raw compiled prompt for backward compatibility
        compiled_prompt = self._assemble_prompt(
            query=query,
            chat_history=chat_history_layer,
            memories=memory_layers,
            workspace_summary=workspace_summary_layer,
            max_tokens=max_tokens,
        )
        context.compiled_prompt = compiled_prompt

        logger.info(
            f"Context compiled - "
            f"Strategy: {compilation_strategy.value}, "
            f"Memories: {len(memory_layers)}, "
            f"Chat history: {len(recent_messages)}, "
            f"Tokens: {token_estimate}/{max_tokens}, "
            f"Time: {compilation_time_ms:.2f}ms"
        )

        return context

    def _get_recent_messages(self, chat_id: str, limit: int) -> List[Message]:
        """Get recent messages from the chat in chronological order."""
        messages = (
            self.db.query(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )
        # Reverse to chronological order
        return list(reversed(messages))

    def _build_chat_history_layer(self, messages: List[Message]) -> ChatHistoryLayer:
        """Build chat history layer from recent messages."""
        message_dicts = [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
            }
            for msg in messages
        ]

        return ChatHistoryLayer(
            messages=message_dicts,
            message_count=len(messages),
        )

    def _build_memory_layers(
        self,
        memories: List[Memory],
        scores: List[float],
        strategy: CompilationStrategy,
    ) -> List[MemoryLayer]:
        """Build memory layers from retrieved memories."""
        if not memories:
            return []

        memory_layers = []
        for memory, score in zip(memories, scores):
            layer = MemoryLayer(
                id=memory.id,
                content=memory.summary or memory.raw_content,
                source_type=memory.source_type,
                importance_score=memory.importance_score,
                similarity_score=score,
                timestamp=memory.timestamp,
                metadata=memory.extra_metadata or {},
            )
            memory_layers.append(layer)

        return memory_layers

    def _build_workspace_summary_layer(
        self, workspace_id: str
    ) -> WorkspaceSummaryLayer:
        """Build workspace summary layer."""
        workspace = (
            self.db.query(Workspace).filter(Workspace.id == workspace_id).first()
        )

        if workspace:
            # TODO: Fetch actual summary from WorkspaceSummary table once implemented
            summary = f"Workspace: {workspace.name}"
            if workspace.description:
                summary += f"\nDescription: {workspace.description}"

            return WorkspaceSummaryLayer(
                summary=summary,
                key_topics=[],  # TODO: Extract from workspace metadata
                summary_timestamp=datetime.now(timezone.utc),
            )

        return WorkspaceSummaryLayer()

    def _estimate_total_tokens(
        self,
        chat_history: ChatHistoryLayer,
        memories: List[MemoryLayer],
        workspace_summary: WorkspaceSummaryLayer,
        query: str,
    ) -> int:
        """Estimate total token count for all layers."""
        token_count = 0

        # Chat history tokens
        for msg in chat_history.messages:
            token_count += self._estimate_tokens(msg.get("content", ""))

        # Memory tokens
        for memory in memories:
            token_count += self._estimate_tokens(memory.content)

        # Workspace summary tokens
        if workspace_summary.summary:
            token_count += self._estimate_tokens(workspace_summary.summary)

        # Query tokens
        token_count += self._estimate_tokens(query)

        # Add overhead for formatting (~20%)
        token_count = int(token_count * 1.2)

        return token_count

    def _assemble_prompt(
        self,
        query: str,
        chat_history: ChatHistoryLayer,
        memories: List[MemoryLayer],
        workspace_summary: WorkspaceSummaryLayer,
        max_tokens: int = 2000,
    ) -> str:
        """Assemble raw compiled prompt from context layers."""
        parts = []

        # Workspace context
        if workspace_summary.summary:
            parts.append(f"## Workspace Context\n{workspace_summary.summary}")

        # Workspace topics
        if workspace_summary.key_topics:
            topics_str = ", ".join(workspace_summary.key_topics)
            parts.append(f"## Key Topics\n{topics_str}")

        # Relevant memories
        if memories:
            memory_section = ["## Relevant Context from Memory"]
            for memory in memories:
                memory_section.append(
                    f"[Similarity: {memory.similarity_score:.0%}] {memory.content[:200]}"
                )
            parts.append("\n".join(memory_section))

        # Recent chat history
        if chat_history.messages:
            chat_section = ["## Recent Conversation"]
            for msg in chat_history.messages:
                role = "User" if msg["role"] == "user" else "Assistant"
                content = msg["content"][:200]
                chat_section.append(f"{role}: {content}")
            parts.append("\n".join(chat_section))

        # Current query
        parts.append(f"## Current Query\n{query}")

        full_prompt = "\n\n".join(parts)

        # Truncate if needed
        if self._estimate_tokens(full_prompt) > max_tokens:
            full_prompt = self._truncate_prompt(full_prompt, max_tokens)

        return full_prompt

    def _estimate_tokens(self, text: str) -> int:
        """Rough estimate of token count (4 chars ≈ 1 token)."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    def _truncate_prompt(self, prompt: str, max_tokens: int) -> str:
        """Truncate prompt to fit token limit."""
        max_chars = max_tokens * 4
        if len(prompt) > max_chars:
            return prompt[:max_chars] + "\n\n...[truncated]"
        return prompt
