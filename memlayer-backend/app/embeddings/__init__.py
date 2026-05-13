"""
Embedding Factory - Phase D1.9
Manages embedding provider selection with fallback logic.
Priority: Mistral > Gemini > OpenAI > SentenceTransformers > Deterministic
"""

from typing import List, Optional
from app.embeddings.base import IEmbeddingProvider, EmbeddingMetadata
from app.embeddings.mistral_provider import MistralEmbeddingProvider
from app.embeddings.gemini_provider import GeminiEmbeddingProvider
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
        1. Mistral (if API key available) - 1024 dimensions
        2. Gemini (if API key available) - 768 dimensions
        3. OpenAI (if API key available) - 1536 dimensions
        4. SentenceTransformers (if model available)
        5. Deterministic (always available - FAILURE STATE)

        SKIPs providers that fail during initialization or embedding generation.
        """
        # Clear provider if it previously failed
        if self._provider is not None:
            # Check if it's the deterministic fallback (failure state)
            if isinstance(self._provider, DeterministicEmbeddingProvider):
                # Try other providers again
                self._provider = None

        # Priority 1: Mistral
        if preferred in ("auto", "mistral", None):
            try:
                provider = MistralEmbeddingProvider()
                # Test if it works
                _ = provider.embed_text("test")
                print(">>> Using MISTRAL embedding provider (1024-dim)")
                self._provider = provider
                return self._provider
            except Exception as e:
                print(f"Mistral failed: {e}")

        # Priority 2: Gemini
        if preferred in ("auto", "gemini", None):
            try:
                provider = GeminiEmbeddingProvider()
                # Test if it works
                _ = provider.embed_text("test")
                print(">>> Using GEMINI embedding provider (768-dim)")
                self._provider = provider
                return self._provider
            except Exception as e:
                print(f"Gemini failed: {e}")

        # Priority 3: OpenAI
        if preferred in ("auto", "openai", None):
            try:
                provider = OpenAIEmbeddingProvider()
                # Test if it works
                _ = provider.embed_text("test")
                print(">>> Using OPENAI embedding provider (1536-dim)")
                self._provider = provider
                return self._provider
            except Exception as e:
                print(f"OpenAI failed: {e}")

        # Priority 4: SentenceTransformers
        if preferred in ("auto", "sentence-transformers", None):
            try:
                provider = SentenceTransformerProvider()
                # Test if it works
                _ = provider.embed_text("test")
                print(">>> Using SentenceTransformer embedding provider")
                self._provider = provider
                return self._provider
            except Exception as e:
                print(f"SentenceTransformers failed: {e}")

        # FAILURE: Fallback to deterministic (NOT REAL SEMANTICS)
        print(
            ">>> WARNING: All real embedding providers failed. Using deterministic fallback - NOT REAL SEMANTICS <<<"
        )
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

    def get_current_provider_name(self) -> str:
        """Get the name of the currently active provider."""
        return self.get_provider().provider_name

    def get_current_dimension(self) -> int:
        """Get the dimension of the currently active provider."""
        return self.get_provider().dimension


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
