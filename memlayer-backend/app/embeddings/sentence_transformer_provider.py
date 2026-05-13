"""
Sentence Transformer Provider - Phase D1.8
Local sentence-transformers for high-quality semantic embeddings.
"""

from typing import List
from app.embeddings.base import IEmbeddingProvider, EmbeddingMetadata
from app.core.config import settings


class SentenceTransformerProvider(IEmbeddingProvider):
    """Local sentence-transformers provider."""

    def __init__(self, model_name: str = None):
        self._model_name = model_name or settings.embedding_model
        self._model = None

    def _get_model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self._model_name)
            except Exception:
                return None
        return self._model

    @property
    def provider_name(self) -> str:
        return "sentence-transformers"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        model = self._get_model()
        if model:
            return model.get_sentence_embedding_dimension()
        return settings.embedding_dim

    @property
    def version(self) -> str:
        return f"{self._model_name}-2024"

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        model = self._get_model()
        if not model:
            raise RuntimeError("SentenceTransformer model not available")

        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        model = self._get_model()
        if not model:
            raise RuntimeError("SentenceTransformer model not available")

        embeddings = model.encode(texts, convert_to_numpy=True, batch_size=32)
        if embeddings.ndim == 1:
            return [embeddings.tolist()]
        return embeddings.tolist()

    def is_available(self) -> bool:
        """Check if provider is available."""
        return self._get_model() is not None
