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
from pgvector.sqlalchemy import Vector
from datetime import datetime
import uuid

Base = declarative_base()


class Workspace(Base):
    """Represents a user's persistent workspace."""

    __tablename__ = "workspaces"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    chats = relationship(
        "Chat", back_populates="workspace", cascade="all, delete-orphan"
    )
    memories = relationship(
        "Memory", back_populates="workspace", cascade="all, delete-orphan"
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
    source_type = Column(
        String, nullable=False
    )  # "user_message", "assistant_response", "file_upload", etc.
    raw_content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    embedding = Column(Vector(384), nullable=True)  # Matches embedding_dim in config
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    importance_score = Column(Float, default=0.5, nullable=False)
    metadata = Column(JSON, default={}, nullable=True)

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

    def __repr__(self):
        return f"<MemoryRetrieval {self.id}>"
