"""
SQLAlchemy models for the semantic memory system.
"""

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Float,
    Integer,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

try:
    from pgvector.sqlalchemy import Vector

    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False
    from sqlalchemy import TypeDecorator, String
    import json

    class Vector(TypeDecorator):
        """Fallback Vector type for when pgvector is unavailable."""

        impl = String

        def __init__(self, dim=384):
            super().__init__()
            self.dim = dim

        def process_bind_param(self, value, dialect):
            if value is not None:
                return json.dumps(value)
            return value

        def process_result_value(self, value, dialect):
            if value is not None:
                return json.loads(value)
            return value


from datetime import datetime
import uuid

Base = declarative_base()


class Workspace(Base):
    """Represents a user's persistent workspace."""

    __tablename__ = "workspaces"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, nullable=False, default="default")
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Multi-model support
    default_provider = Column(
        String, default="gemini", nullable=False
    )  # gemini, openai, claude

    # Workspace state tracking
    memory_count = Column(Integer, default=0, nullable=False)
    last_memory_timestamp = Column(DateTime, nullable=True)

    # Relationships
    chats = relationship(
        "Chat", back_populates="workspace", cascade="all, delete-orphan"
    )
    memories = relationship(
        "Memory", back_populates="workspace", cascade="all, delete-orphan"
    )
    workspace_summary = relationship(
        "WorkspaceSummary",
        back_populates="workspace",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Workspace {self.id}: {self.name}>"


class Chat(Base):
    """Represents a persistent conversation session."""

    __tablename__ = "chats"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    workspace = relationship("Workspace", back_populates="chats")
    messages = relationship(
        "Message", back_populates="chat", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Chat {self.id}>"


class Message(Base):
    """Represents a single message in a chat."""

    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_id = Column(String, ForeignKey("chats.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    chat = relationship("Chat", back_populates="messages")

    def __repr__(self):
        return f"<Message {self.id}>"


class Memory(Base):
    """Represents a semantic memory object."""

    __tablename__ = "memories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    tenant_id = Column(String, nullable=False, default="default")
    source_type = Column(
        String, nullable=False
    )  # "user_message", "assistant_response", "file_upload", "generated", etc.
    raw_content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    embedding = Column(
        Vector(384) if VECTOR_AVAILABLE else JSON, nullable=True
    )  # 384-dim embedding vector
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    importance_score = Column(Float, default=0.5, nullable=False)
    extra_metadata = Column("metadata", JSON, default={}, nullable=True)

    # Lineage tracking for memory graphs
    source_memory_ids = Column(
        JSON, default=[], nullable=True
    )  # IDs of memories this came from
    generated_from_message_id = Column(String, nullable=True)  # Original message ID
    generated_by_provider = Column(
        String, nullable=True
    )  # Which provider generated this
    generation_timestamp = Column(
        DateTime(timezone=True), nullable=True
    )  # When it was generated

    # Relationships
    workspace = relationship("Workspace", back_populates="memories")

    def __repr__(self):
        return f"<Memory {self.id}>"


class MemoryRetrieval(Base):
    """Tracks memory retrievals for analytics and optimization."""

    __tablename__ = "memory_retrievals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    query = Column(Text, nullable=False)
    retrieved_memory_ids = Column(JSON, default=[], nullable=True)
    similarity_scores = Column(JSON, default=[], nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Context metadata
    provider_used = Column(String, nullable=True)  # Which provider was this for
    total_retrieved = Column(Integer, default=0, nullable=False)
    latency_ms = Column(Float, nullable=True)  # How long retrieval took
    success = Column(String, default="true", nullable=False)  # true/false/error

    def __repr__(self):
        return f"<MemoryRetrieval {self.id}>"


class WorkspaceSummary(Base):
    """Persistent high-level summary of workspace state."""

    __tablename__ = "workspace_summaries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(
        String, ForeignKey("workspaces.id"), unique=True, nullable=False
    )

    # Summary content
    summary_text = Column(Text, nullable=True)  # Compressed workspace state
    summary_embedding = Column(
        Vector(384), nullable=True
    )  # Embedded summary for retrieval

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # State
    total_messages = Column(Integer, default=0, nullable=False)
    total_memories = Column(Integer, default=0, nullable=False)
    key_topics = Column(JSON, default=[], nullable=True)  # Emerging topics in workspace

    # Lineage
    generated_from_message_count = Column(Integer, default=0, nullable=False)
    last_summary_trigger_reason = Column(
        String, nullable=True
    )  # "time", "message_count", "manual"

    # Relationships
    workspace = relationship("Workspace", back_populates="workspace_summary")

    def __repr__(self):
        return f"<WorkspaceSummary {self.workspace_id}>"


class ContextCompilation(Base):
    """Records of compiled contexts for debugging and optimization."""

    __tablename__ = "context_compilations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    chat_id = Column(String, nullable=True)  # Which chat (if any)

    # What was compiled
    query = Column(Text, nullable=False)
    compiled_prompt = Column(Text, nullable=False)

    # How it was compiled
    provider = Column(String, nullable=False)
    strategy = Column(String, nullable=False)  # "full_context", "compressed", "minimal"

    # Metadata
    memory_ids_used = Column(JSON, default=[], nullable=True)
    memory_count = Column(Integer, default=0, nullable=False)
    recent_message_count = Column(Integer, default=0, nullable=False)

    # Metrics
    token_estimate = Column(Integer, default=0, nullable=False)
    compilation_time_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ContextCompilation {self.id}>"


class ReplayTrace(Base):
    """Immutable record of runtime executions for deterministic replay."""

    __tablename__ = "replay_traces"

    trace_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    tenant_id = Column(String, nullable=False, default="default")

    query = Column(Text, nullable=False)
    query_type = Column(String, nullable=True)
    provider = Column(String, nullable=False)
    compression_mode = Column(String, nullable=False)
    token_budget = Column(Integer, nullable=False)

    # Deterministic State
    execution_plan = Column(JSON, nullable=False)  # Canonical JSON
    trace_data = Column(JSON, nullable=False)  # Full stage metrics
    integrity_hash = Column(String(64), nullable=False)

    # Results
    quality_score = Column(Float, default=0.0)
    semantic_retention = Column(Float, default=0.0)
    token_efficiency = Column(Float, default=0.0)
    total_duration_ms = Column(Float, default=0.0)

    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ReplayTrace {self.trace_id}>"


class SemanticLineage(Base):
    """Recursive ancestry tracking for cognition state."""

    __tablename__ = "semantic_lineage"

    checkpoint_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    tenant_id = Column(String, nullable=False, default="default")

    state_hash = Column(String(64), nullable=False)
    parent_id = Column(
        String, ForeignKey("semantic_lineage.checkpoint_id"), nullable=True
    )
    operation_id = Column(String, nullable=False)

    extra_metadata = Column("metadata", JSON, default={}, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SemanticLineage {self.checkpoint_id}>"


class GovernanceAudit(Base):
    """Immutable append-only audit trail."""

    __tablename__ = "governance_audit"

    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    tenant_id = Column(String, nullable=False, default="default")

    event_type = Column(String(100), nullable=False)
    event_data = Column(JSON, nullable=False)
    integrity_hash = Column(String(64), nullable=False)
    recorded_by = Column(String(100), nullable=False)

    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<GovernanceAudit {self.audit_id}>"


class TelemetryEvent(Base):
    """Time-series telemetry events linked to traces."""

    __tablename__ = "telemetry_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(String, ForeignKey("replay_traces.trace_id"), nullable=False)
    tenant_id = Column(String, nullable=False, default="default")

    stage = Column(String(50), nullable=False)
    duration_ms = Column(Float, nullable=True)
    token_metrics = Column(JSON, nullable=True)

    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<TelemetryEvent {self.id}>"
