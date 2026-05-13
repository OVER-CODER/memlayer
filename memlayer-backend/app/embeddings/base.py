"""
Embedding Provider Interface - Phase D1.8
Abstract interface for semantic embedding providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import hashlib
import json


@dataclass
class EmbeddingMetadata:
    """Metadata for embeddings - ensures replay determinism."""

    provider: str
    model: str
    version: str
    checksum: str  # Hash of the embedding for verification
    dimension: int
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "version": self.version,
            "checksum": self.checksum,
            "dimension": self.dimension,
            "created_at": self.created_at,
        }


class IEmbeddingProvider(ABC):
    """Abstract interface for embedding providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding dimension."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Model version for reproducibility."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass

    def compute_checksum(self, embedding: List[float]) -> str:
        """Compute deterministic checksum for an embedding."""
        return hashlib.sha256(
            json.dumps(embedding, sort_keys=True).encode()
        ).hexdigest()[:16]

    def create_metadata(self, embedding: List[float]) -> EmbeddingMetadata:
        """Create metadata for an embedding."""
        from datetime import datetime, timezone

        return EmbeddingMetadata(
            provider=self.provider_name,
            model=self.model_name,
            version=self.version,
            checksum=self.compute_checksum(embedding),
            dimension=self.dimension,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
