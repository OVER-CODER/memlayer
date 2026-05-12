"""
Context schemas for structured context representation.

Defines the layered context structure that providers receive,
including chat history, semantic memories, workspace summary, and metadata.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum


class CompilationStrategy(str, Enum):
    """Context compilation strategies."""

    FULL_CONTEXT = "full_context"  # Include all memories
    COMPRESSED = "compressed"  # Compress memories with summaries
    MINIMAL = "minimal"  # Only most relevant memories


class MemoryLayer(BaseModel):
    """A semantic memory in the context."""

    id: str = Field(..., description="Memory ID")
    content: str = Field(..., description="Memory content")
    source_type: str = Field(
        ..., description="Source type (user_message, assistant_response, etc)"
    )
    importance_score: float = Field(..., description="Importance score (0-1)")
    similarity_score: float = Field(0.0, description="Similarity to query (0-1)")
    timestamp: datetime = Field(..., description="When memory was created")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ChatHistoryLayer(BaseModel):
    """Recent chat history in the context."""

    messages: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Recent messages [{'role': 'user'|'assistant', 'content': '...', 'timestamp': '...'}]",
    )
    message_count: int = Field(
        default=0, description="Number of recent messages included"
    )


class WorkspaceSummaryLayer(BaseModel):
    """Persistent high-level workspace state."""

    summary: Optional[str] = Field(
        None, description="High-level summary of workspace state"
    )
    key_topics: List[str] = Field(
        default_factory=list, description="Emerging topics in the workspace"
    )
    summary_timestamp: Optional[datetime] = Field(
        None, description="When the summary was last updated"
    )


class CompilationMetadata(BaseModel):
    """Metadata about context compilation."""

    provider: str = Field(..., description="Provider that will receive this context")
    model: str = Field(..., description="Model that will be used")
    compilation_strategy: CompilationStrategy = Field(
        ..., description="Strategy used to compile context"
    )
    token_estimate: int = Field(..., description="Estimated token count")
    token_limit: int = Field(..., description="Max tokens available")
    retrieved_memory_ids: List[str] = Field(
        default_factory=list, description="IDs of memories retrieved"
    )
    retrieved_scores: List[float] = Field(
        default_factory=list, description="Similarity scores for retrieved memories"
    )
    compilation_time_ms: float = Field(0.0, description="Time to compile context (ms)")
    latency_ms: float = Field(0.0, description="Generation latency (ms)")


class ContextLayers(BaseModel):
    """Structured context with distinct composable layers.

    This represents the complete context being sent to an LLM provider,
    organized into semantic layers that providers can format as needed.
    """

    # The actual layers
    chat_history: ChatHistoryLayer = Field(..., description="Recent chat messages")
    semantic_memories: List[MemoryLayer] = Field(
        default_factory=list,
        description="Retrieved semantic memories with relevance scores",
    )
    workspace_summary: WorkspaceSummaryLayer = Field(
        default_factory=WorkspaceSummaryLayer,
        description="Persistent high-level workspace state",
    )

    # Metadata about this compilation
    metadata: CompilationMetadata = Field(
        ..., description="Metadata about this context compilation"
    )

    # The raw compiled prompt (for backward compatibility and debugging)
    compiled_prompt: Optional[str] = Field(
        None, description="Raw compiled prompt (set by compilation service)"
    )

    class Config:
        use_enum_values = True


class ContextDebugInfo(BaseModel):
    """Debug information about context compilation and generation."""

    context_layers: ContextLayers = Field(..., description="The structured context")
    compiled_prompt: str = Field(
        ..., description="Raw compiled prompt sent to provider"
    )
    generation_result: Optional[Dict[str, Any]] = Field(
        None, description="Generation result from provider"
    )
    tokens_used: int = Field(0, description="Actual tokens used by generation")
    latency_ms: float = Field(0.0, description="Generation latency")

    class Config:
        use_enum_values = True
