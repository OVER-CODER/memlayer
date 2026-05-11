"""
Core configuration for the memlayer backend.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://localhost/memlayer_dev"

    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # LLM
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-pro"

    # Memory
    memory_chunk_size: int = 500
    top_k_memories: int = 5
    memory_retrieval_threshold: float = 0.3

    # Server
    debug: bool = False
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
