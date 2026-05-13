"""
Core configuration for the memlayer backend.
Production-ready with validation and secure defaults.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import ConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(
        extra="ignore",  # Allow extra fields in .env without breaking
        case_sensitive=False,
    )

    # Security
    secret_key: str = "dev_secret_key_change_me_in_production_deterministic_spine"
    security_enabled: bool = True
    api_key_header_name: str = "X-API-Key"
    jwt_algorithm: str = "HS256"

    # Server
    debug: bool = False
    log_level: str = "INFO"
    port: int = 8000
    app_current_tenant_id: str = "default"

    # Database - Support both SQLite (dev) and PostgreSQL (prod)
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://memlayer:memlayer@localhost:5432/memlayer"
    )
    async_database_url: str = os.getenv(
        "ASYNC_DATABASE_URL",
        "postgresql+asyncpg://memlayer:memlayer@localhost:5432/memlayer",
    )

    # Supabase (legacy - optional)
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None

    # Redis (Operational Coordination)
    redis_url: Optional[str] = None
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # Object Storage (Snapshots/Archives)
    storage_provider: str = "local"
    storage_local_path: str = "./.memlayer/storage"
    s3_bucket: str = "memlayer-snapshots"
    s3_region: str = "us-east-1"
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    s3_endpoint_url: Optional[str] = None

    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384
    mistral_api_key: Optional[str] = None

    # LLM Providers
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-pro"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # Default provider and model
    default_provider: str = "gemini"
    default_model: str = "gemini-pro"

    # Runtime Determinism
    deterministic_mode: bool = True
    serialization_stable_keys: bool = True

    # Memory
    memory_chunk_size: int = 500
    top_k_memories: int = 5
    memory_retrieval_threshold: float = 0.3

    def validate_production(self):
        """Validate required settings for production."""
        issues = []

        # Check for SQLite (should not be in production)
        if "sqlite" in self.database_url.lower():
            issues.append("DATABASE_URL is SQLite - not suitable for production")

        # Check for default secret key
        if (
            self.secret_key
            == "dev_secret_key_change_me_in_production_deterministic_spine"
        ):
            issues.append("SECRET_KEY is still using default value")

        # Check for missing LLM keys
        if not self.gemini_api_key and not self.openai_api_key:
            issues.append("No LLM API key configured")

        return issues


settings = Settings()
