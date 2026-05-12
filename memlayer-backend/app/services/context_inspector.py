"""
Context Inspection Service - Tools for debugging and analyzing context compilation.

This service provides utilities for examining how context is compiled,
retrieved, and used by different providers.
"""

from typing import Optional, Dict, Any
from app.schemas.context import ContextLayers, ContextDebugInfo
from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger(__name__)


class ContextInspector:
    """Provides debugging and inspection tools for context compilation.

    Features:
    - View compiled prompts by layer
    - Analyze token distribution
    - Inspect memory retrieval decisions
    - Compare providers' context formatting
    - Export debug information
    """

    @staticmethod
    def format_context_debug(
        context: ContextLayers,
        compiled_prompt: str,
        generation_metadata: Optional[Dict] = None,
    ) -> ContextDebugInfo:
        """Create debug information for a context compilation.

        Args:
            context: The structured context
            compiled_prompt: The raw compiled prompt
            generation_metadata: Optional metadata from generation

        Returns:
            ContextDebugInfo object with full debugging info
        """
        return ContextDebugInfo(
            context_layers=context,
            compiled_prompt=compiled_prompt,
            generation_result=generation_metadata,
            tokens_used=generation_metadata.get("tokens_used", 0)
            if generation_metadata
            else 0,
            latency_ms=generation_metadata.get("latency_ms", 0)
            if generation_metadata
            else 0,
        )

    @staticmethod
    def inspect_token_distribution(context: ContextLayers) -> Dict[str, int]:
        """Analyze token distribution across context layers.

        Args:
            context: The structured context

        Returns:
            Dictionary with token counts per layer
        """
        distribution = {}

        # Chat history tokens
        chat_tokens = 0
        for msg in context.chat_history.messages:
            chat_tokens += len(msg.get("content", "")) // 4

        distribution["chat_history"] = chat_tokens

        # Memory tokens
        memory_tokens = 0
        for memory in context.semantic_memories:
            memory_tokens += len(memory.content) // 4

        distribution["semantic_memories"] = memory_tokens

        # Workspace summary tokens
        summary_tokens = 0
        if context.workspace_summary.summary:
            summary_tokens = len(context.workspace_summary.summary) // 4

        distribution["workspace_summary"] = summary_tokens

        # Metadata overhead
        distribution["metadata_overhead"] = context.metadata.token_estimate - (
            chat_tokens + memory_tokens + summary_tokens
        )

        distribution["total"] = context.metadata.token_estimate

        return distribution

    @staticmethod
    def format_context_report(context: ContextLayers) -> str:
        """Generate a human-readable context report.

        Args:
            context: The structured context

        Returns:
            Formatted report string
        """
        lines = []

        lines.append("=" * 80)
        lines.append("CONTEXT COMPILATION REPORT")
        lines.append("=" * 80)

        # Metadata
        lines.append("\n## COMPILATION METADATA")
        lines.append(f"Provider: {context.metadata.provider}")
        lines.append(f"Model: {context.metadata.model}")
        lines.append(f"Strategy: {context.metadata.compilation_strategy.value}")
        lines.append(
            f"Tokens: {context.metadata.token_estimate}/{context.metadata.token_limit}"
        )
        lines.append(f"Compilation Time: {context.metadata.compilation_time_ms:.2f}ms")

        # Chat History
        lines.append("\n## CHAT HISTORY")
        lines.append(f"Messages: {len(context.chat_history.messages)}")
        for i, msg in enumerate(context.chat_history.messages[-3:], 1):  # Last 3
            role = msg["role"].upper()
            content = msg["content"][:100]
            lines.append(f"  {i}. {role}: {content}...")

        # Semantic Memories
        lines.append("\n## SEMANTIC MEMORIES")
        lines.append(f"Count: {len(context.semantic_memories)}")
        for i, memory in enumerate(context.semantic_memories[:5], 1):  # Top 5
            lines.append(
                f"  {i}. [{memory.source_type}] "
                f"Similarity: {memory.similarity_score:.0%} "
                f"Importance: {memory.importance_score:.0%}"
            )
            lines.append(f"     {memory.content[:80]}...")

        # Workspace Summary
        lines.append("\n## WORKSPACE SUMMARY")
        if context.workspace_summary.summary:
            lines.append(f"Summary: {context.workspace_summary.summary}")
            if context.workspace_summary.key_topics:
                topics = ", ".join(context.workspace_summary.key_topics)
                lines.append(f"Key Topics: {topics}")
        else:
            lines.append("(No workspace summary yet)")

        # Token Distribution
        lines.append("\n## TOKEN DISTRIBUTION")
        distribution = ContextInspector.inspect_token_distribution(context)
        for layer, tokens in distribution.items():
            if layer != "total":
                percentage = (
                    (tokens / distribution["total"]) * 100
                    if distribution["total"] > 0
                    else 0
                )
                lines.append(f"  {layer}: {tokens} tokens ({percentage:.1f}%)")
        lines.append(f"  TOTAL: {distribution['total']} tokens")

        # Memory Retrieval Stats
        if context.metadata.retrieved_memory_ids:
            lines.append("\n## MEMORY RETRIEVAL")
            lines.append(
                f"Retrieved: {len(context.metadata.retrieved_memory_ids)} memories"
            )
            for mem_id, score in zip(
                context.metadata.retrieved_memory_ids,
                context.metadata.retrieved_scores,
            ):
                lines.append(f"  - {mem_id}: {score:.0%}")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)

    @staticmethod
    def export_debug_json(
        context: ContextLayers,
        compiled_prompt: str,
        filename: Optional[str] = None,
    ) -> str:
        """Export context debug information as JSON.

        Args:
            context: The structured context
            compiled_prompt: The raw compiled prompt
            filename: Optional file to write to

        Returns:
            JSON string
        """
        debug_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "provider": context.metadata.provider,
                "model": context.metadata.model,
                "strategy": context.metadata.compilation_strategy.value,
                "tokens": {
                    "estimate": context.metadata.token_estimate,
                    "limit": context.metadata.token_limit,
                },
                "compilation_time_ms": context.metadata.compilation_time_ms,
            },
            "chat_history": {
                "message_count": len(context.chat_history.messages),
                "messages": [
                    {
                        "role": msg["role"],
                        "content": msg["content"][:200],
                        "timestamp": msg["timestamp"],
                    }
                    for msg in context.chat_history.messages
                ],
            },
            "semantic_memories": {
                "count": len(context.semantic_memories),
                "memories": [
                    {
                        "id": m.id,
                        "source_type": m.source_type,
                        "similarity_score": m.similarity_score,
                        "importance_score": m.importance_score,
                        "content": m.content[:200],
                    }
                    for m in context.semantic_memories
                ],
            },
            "workspace_summary": {
                "summary": context.workspace_summary.summary,
                "key_topics": context.workspace_summary.key_topics,
            },
            "compiled_prompt_preview": compiled_prompt[:500],
        }

        json_str = json.dumps(debug_data, indent=2)

        if filename:
            with open(filename, "w") as f:
                f.write(json_str)
            logger.info(f"Exported debug info to {filename}")

        return json_str

    @staticmethod
    def compare_providers(
        context: ContextLayers,
        providers: list = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Compare how different providers would format this context.

        Args:
            context: The structured context
            providers: List of provider names to compare (default: all)

        Returns:
            Dictionary with provider-specific formatting info
        """
        if providers is None:
            providers = ["gemini", "openai", "claude"]

        comparison = {}

        for provider_name in providers:
            comparison[provider_name] = {
                "max_tokens": {
                    "gemini": 8192,
                    "openai": 4096,
                    "claude": 4096,
                }.get(provider_name, 2048),
                "supports_streaming": True,
                "formatting": {
                    "uses_markdown": provider_name != "gemini",
                    "system_prompt": True,
                    "token_limit": {
                        "gemini": 8192,
                        "openai": 4096,
                        "claude": 4096,
                    }.get(provider_name, 2048),
                },
            }

        return comparison
