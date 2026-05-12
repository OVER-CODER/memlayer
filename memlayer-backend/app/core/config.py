"""
Core configuration for the memlayer backend.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Security
    secret_key: str = "dev_secret_key_change_me_in_production_deterministic_spine"
    security_enabled: bool = True
    api_key_header_name: str = "X-API-Key"
    jwt_algorithm: str = "HS256"
    
    # Google (Already has gemini_api_key, adding google_api_key for alias)
    google_api_key: Optional[str] = None

    # Database
    database_url: str = "sqlite:///./memlayer.db"
    async_database_url: str = "sqlite+aiosqlite:///./memlayer.db"
    
    # Redis (Operational Coordination)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # Object Storage (Snapshots/Archives)
    storage_provider: str = "local" # local, s3, minio, gcs
    storage_local_path: str = "./.memlayer/storage"
    s3_bucket: str = "memlayer-snapshots"
    s3_region: str = "us-east-1"
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    s3_endpoint_url: Optional[str] = None # For MinIO
    
    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384
    
    # LLM Providers
    gemini_api_key: Optional[str] = None
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
    
    # Server
    debug: bool = False
    log_level: str = "INFO"
    app_current_tenant_id: str = "default"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
