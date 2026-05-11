"""
Context compilation service that assembles compressed context from memories.
"""

from typing import List, Tuple
from app.db.models import Memory, Message
from sqlalchemy.orm import Session
from datetime import datetime, timedelta


class ContextCompilationService:
    """Assembles contextual information from memories and recent chat history."""

    def __init__(self, db: Session):
        self.db = db

    def compile_context(
        self,
        workspace_id: str,
        chat_id: str,
        query: str,
        retrieved_memories: List[Memory],
        retrieved_scores: List[float],
        recent_message_count: int = 10,
        max_tokens: int = 2000,
    ) -> dict:
        """
        Compile a comprehensive context for the LLM.

        Returns a dict with:
        - system_context: Background info about the workspace/user
        - retrieved_memories: Relevant semantic memories
        - recent_chat: Recent conversation context
        - compiled_prompt: Full prompt ready for LLM
        """

        # Get recent chat messages
        recent_messages = self._get_recent_messages(chat_id, recent_message_count)

        # Get workspace info (if any)
        workspace_context = self._get_workspace_context(workspace_id)

        # Build memory snippets
        memory_snippets = self._build_memory_snippets(
            retrieved_memories, retrieved_scores
        )

        # Build chat history
        chat_history = self._build_chat_history(recent_messages)

        # Assemble full context
        compiled_prompt = self._assemble_prompt(
            query=query,
            workspace_context=workspace_context,
            memory_snippets=memory_snippets,
            chat_history=chat_history,
            max_tokens=max_tokens,
        )

        return {
            "workspace_context": workspace_context,
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
                for m, s in zip(retrieved_memories, retrieved_scores)
            ],
            "recent_chat": chat_history,
            "compiled_prompt": compiled_prompt,
            "metadata": {
                "total_memories_used": len(retrieved_memories),
                "recent_messages_included": len(recent_messages),
                "estimated_tokens": self._estimate_tokens(compiled_prompt),
            },
        }

    def _get_recent_messages(self, chat_id: str, limit: int) -> List[Message]:
        """Get recent messages from the chat."""
        return (
            self.db.query(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )

    def _get_workspace_context(self, workspace_id: str) -> str:
        """Get workspace metadata and context."""
        from app.db.models import Workspace

        workspace = (
            self.db.query(Workspace).filter(Workspace.id == workspace_id).first()
        )

        if workspace:
            return f"Workspace: {workspace.name}\nDescription: {workspace.description or 'N/A'}"
        return ""

    def _build_memory_snippets(
        self, memories: List[Memory], scores: List[float]
    ) -> str:
        """Build formatted memory snippets."""
        if not memories:
            return ""

        snippets = ["## Relevant Context from Memory\n"]
        for memory, score in zip(memories, scores):
            snippets.append(
                f"[Similarity: {score:.2%}] {memory.summary or memory.raw_content[:200]}"
            )

        return "\n".join(snippets)

    def _build_chat_history(self, messages: List[Message]) -> str:
        """Build formatted chat history."""
        if not messages:
            return ""

        # Reverse to chronological order
        messages = list(reversed(messages))

        history = ["## Recent Conversation\n"]
        for msg in messages:
            role = "User" if msg.role == "user" else "Assistant"
            history.append(f"{role}: {msg.content[:500]}")

        return "\n".join(history)

    def _assemble_prompt(
        self,
        query: str,
        workspace_context: str,
        memory_snippets: str,
        chat_history: str,
        max_tokens: int = 2000,
    ) -> str:
        """Assemble the final prompt for the LLM."""

        parts = []

        if workspace_context:
            parts.append(workspace_context)

        if memory_snippets:
            parts.append(memory_snippets)

        if chat_history:
            parts.append(chat_history)

        parts.append(f"## Current Query\n{query}")

        full_prompt = "\n\n".join(parts)

        # Truncate if needed
        if self._estimate_tokens(full_prompt) > max_tokens:
            full_prompt = self._truncate_prompt(full_prompt, max_tokens)

        return full_prompt

    def _estimate_tokens(self, text: str) -> int:
        """Rough estimate of token count (4 chars ≈ 1 token)."""
        return len(text) // 4

    def _truncate_prompt(self, prompt: str, max_tokens: int) -> str:
        """Truncate prompt to fit token limit."""
        max_chars = max_tokens * 4
        if len(prompt) > max_chars:
            return prompt[:max_chars] + "...[truncated]"
        return prompt
