"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Workspace Schemas
class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Chat Schemas
class ChatCreate(BaseModel):
    title: Optional[str] = None


class ChatResponse(BaseModel):
    id: str
    workspace_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Message Schemas
class MessageCreate(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class MessageResponse(BaseModel):
    id: str
    chat_id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# Memory Schemas
class MemoryCreate(BaseModel):
    raw_content: str
    source_type: str = "user_message"
    summary: Optional[str] = None
    importance_score: float = 0.5
    metadata: Optional[dict] = None


class MemoryResponse(BaseModel):
    id: str
    workspace_id: str
    source_type: str
    raw_content: str
    summary: Optional[str]
    importance_score: float
    timestamp: datetime
    metadata: Optional[dict]

    class Config:
        from_attributes = True


# Query/Response Schemas
class ChatQueryRequest(BaseModel):
    query: str
    top_k_memories: int = 5
    similarity_threshold: float = 0.3
    provider: Optional[str] = (
        None  # Optional provider override (gemini, openai, claude)
    )
    model: Optional[str] = None  # Optional model override


class RetrievedMemory(BaseModel):
    id: str
    content: str
    summary: Optional[str]
    source_type: str
    similarity_score: float
    importance_score: float
    timestamp: datetime


class ChatQueryResponse(BaseModel):
    message_id: str
    response: str
    provider_used: str  # Provider that was used
    model_used: str  # Model that was used
    tokens_used: int  # Tokens used by generation
    latency_ms: float  # Generation latency
    retrieved_memories: List[RetrievedMemory]
    context_metadata: dict


# Analytics Schemas
class MemoryStats(BaseModel):
    total_memories: int
    by_source: dict
    avg_importance: float
    oldest_memory: Optional[datetime]
    newest_memory: Optional[datetime]


class RetrievalStats(BaseModel):
    total_retrievals: int
    avg_similarity: float = 0.0
    max_similarity: float = 0.0
    min_similarity: float = 0.0
