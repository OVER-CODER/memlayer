"""
Embedding Factory - Phase D1.8
Manages embedding provider selection with fallback logic.
"""

from typing import List, Optional
from app.embeddings.base import IEmbeddingProvider, EmbeddingMetadata
from app.embeddings.openai_provider import OpenAIEmbeddingProvider
from app.embeddings.sentence_transformer_provider import SentenceTransformerProvider
from app.embeddings.deterministic import DeterministicEmbeddingProvider


class EmbeddingFactory:
    """Factory for creating and managing embedding providers."""

    _instance: Optional["EmbeddingFactory"] = None
    _provider: Optional[IEmbeddingProvider] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_provider(self, preferred: str = "auto") -> IEmbeddingProvider:
        """
        Get embedding provider with automatic fallback.

        Priority:
        1. OpenAI (if API key available)
        2. SentenceTransformers (if model available)
        3. Deterministic (always available)
        """
        if self._provider is not None:
            return self._provider

        if preferred == "openai":
            provider = OpenAIEmbeddingProvider()
            if provider.is_available():
                self._provider = provider
                return provider

        if preferred in ("auto", "sentence-transformers"):
            provider = SentenceTransformerProvider()
            if provider.is_available():
                self._provider = provider
                return provider

        # Fallback to deterministic
        self._provider = DeterministicEmbeddingProvider()
        return self._provider

    def reset(self):
        """Reset provider (for testing)."""
        self._provider = None

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding using the best available provider."""
        provider = self.get_provider()
        return provider.embed_text(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        provider = self.get_provider()
        return provider.embed_batch(texts)

    def get_metadata(self, text: str) -> EmbeddingMetadata:
        """Get embedding with metadata."""
        provider = self.get_provider()
        embedding = provider.embed_text(text)
        return provider.create_metadata(embedding)


# Global factory instance
_embedding_factory: Optional[EmbeddingFactory] = None


def get_embedding_factory() -> EmbeddingFactory:
    """Get the global embedding factory."""
    global _embedding_factory
    if _embedding_factory is None:
        _embedding_factory = EmbeddingFactory()
    return _embedding_factory


def embed_text(text: str) -> List[float]:
    """Convenience function for embedding."""
    return get_embedding_factory().embed_text(text)


def embed_batch(texts: List[str]) -> List[List[float]]:
    """Convenience function for batch embedding."""
    return get_embedding_factory().embed_batch(texts)
