"""
Embedding service - Abstract layer for embedding generation.
Supports both local models and API-based embeddings.
"""

from abc import ABC, abstractmethod
from typing import List, Union
from sentence_transformers import SentenceTransformer
import numpy as np
from app.core.config import settings


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def embed(
        self, text: Union[str, List[str]]
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text(s)."""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        pass


class SentenceTransformersProvider(EmbeddingProvider):
    """Local embedding provider using sentence-transformers."""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.embedding_model
        self.model = SentenceTransformer(self.model_name)

    def embed(
        self, text: Union[str, List[str]]
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings using sentence-transformers."""
        embeddings = self.model.encode(text, convert_to_numpy=True)

        # Convert to list for JSON serialization
        if isinstance(embeddings, np.ndarray):
            if embeddings.ndim == 1:
                return embeddings.tolist()
            else:
                return embeddings.tolist()
        return embeddings

    def get_dimension(self) -> int:
        """Get embedding dimension from model."""
        return self.model.get_sentence_embedding_dimension()


class EmbeddingService:
    """Service for text embedding with pluggable providers."""

    def __init__(self, provider: EmbeddingProvider = None):
        self.provider = provider or SentenceTransformersProvider()

    def embed(
        self, text: Union[str, List[str]]
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings."""
        return self.provider.embed(text)

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Embed multiple texts efficiently."""
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = self.embed(batch)
            if isinstance(batch_embeddings[0], (list, np.ndarray)):
                embeddings.extend(batch_embeddings)
            else:
                embeddings.append(batch_embeddings)
        return embeddings


# Global embedding service instance
_embedding_service: EmbeddingService = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
