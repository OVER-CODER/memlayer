"""
Embedding service - Abstract layer for embedding generation.
Supports both local models and API-based embeddings.
"""

from abc import ABC, abstractmethod
from typing import List, Union
import hashlib
import re

try:
    from sentence_transformers import SentenceTransformer
except (ImportError, ValueError, Exception):
    SentenceTransformer = None
import numpy as np
from app.core.config import settings

# TF-IDF for semantic embeddings
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    TFIDF_AVAILABLE = True
except ImportError:
    TFIDF_AVAILABLE = False


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

        if isinstance(embeddings, np.ndarray):
            if embeddings.ndim == 1:
                return embeddings.tolist()
            else:
                return embeddings.tolist()
        return embeddings

    def get_dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()


class TFIDFEmbeddingProvider(EmbeddingProvider):
    """TF-IDF based semantic embeddings for when ML models unavailable."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.vectorizer = None
        self._vocabulary = None
        self._idf = None

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        return text.split()

    def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate TF-IDF based embeddings."""
        if isinstance(text, str):
            text = [text]

        # Build vocabulary from all texts
        all_tokens = set()
        tokenized = []
        for t in text:
            tokens = self._tokenize(t)
            tokenized.append(tokens)
            all_tokens.update(tokens)

        # Use top dimension terms
        vocab = list(all_tokens)[:self.dimension]
        vocab_map = {w: i for i, w in enumerate(vocab)}

        # Build TF-IDF vectors
        embeddings = []
        for tokens in tokenized:
            vector = [0.0] * self.dimension
            token_counts = {}
            for token in tokens:
                token_counts[token] = token_counts.get(token, 0) +

            for token, count in token_counts.items():
                if token in vocab_map:
                    idx = vocab_map[token]
                    # Use count as simple TF (could add IDF)
                    vector[idx] = count / max(len(tokens), 1)

            # Normalize
            norm = np.sqrt(sum(v * v for v in vector))
            if norm > 0:
                vector = [v / norm for v in vector]
            embeddings.append(vector)

        return embeddings[0] if len(text) == 1 else embeddings

    def get_dimension(self) -> int:
        return self.dimension


class DeterministicHashEmbeddingProvider(EmbeddingProvider):
    """Deterministic hash-based embeddings for reproducible results."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _get_deterministic_vector(self, text: str) -> List[float]:
        """Generate deterministic vector from text hash."""
        text_lower = text.lower()
        words = text_lower.split()

        vector = [0.0] * self.dimension

        # Use each word to influence multiple dimensions
        for i, word in enumerate(words):
            word_hash = hashlib.sha256(word.encode()).hexdigest()

            # Convert hash to numbers and fill vector
            for j in range(min(8, self.dimension // len(words) if words else 1)):
                idx = (i * 8 + j) % self.dimension
                # Use pairs of hex chars to create float values
                val = int(word_hash[j*4:j*4+4], 16) / 65535.0
                vector[idx] = (vector[idx] + val) / 2

        # Normalize
        norm = np.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate deterministic embeddings."""
        if isinstance(text, str):
            return self._get_deterministic_vector(text)
        return [self._get_deterministic_vector(t) for t in text]

    def get_dimension(self) -> int:
        return self.dimension


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for local testing without large dependencies."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def embed(
        self, text: Union[str, List[str]]
    ) -> Union[List[float], List[List[float]]]:
        """Generate random embeddings."""
        if isinstance(text, list):
            return [np.random.rand(self.dimension).tolist() for _ in text]
        return np.random.rand(self.dimension).tolist()

    def get_dimension(self) -> int:
        return self.dimension


class EmbeddingService:
    """Service for text embedding with pluggable providers."""

    def __init__(self, provider: EmbeddingProvider = None):
        self.provider = provider if provider is not None else get_default_provider()

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


def get_default_provider() -> EmbeddingProvider:
    """Get the default embedding provider, with automatic fallback."""
    if SentenceTransformer is not None:
        try:
            return SentenceTransformersProvider()
        except Exception:
            pass

    # Use TF-IDF if available, otherwise deterministic hash
    if TFIDF_AVAILABLE:
        try:
            return TFIDFEmbeddingProvider()
        except Exception:
            pass

    return DeterministicHashEmbeddingProvider()


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service."""
    import os

    global _embedding_service
    if _embedding_service is None:
        use_mock = os.getenv("USE_MOCK_EMBEDDINGS", "false").lower() == "true"

        if use_mock:
            _embedding_service = EmbeddingService(MockEmbeddingProvider())
        elif SentenceTransformer is not None:
            try:
                _embedding_service = EmbeddingService()
            except Exception:
                _embedding_service = EmbeddingService(MockEmbeddingProvider())
        else:
            _embedding_service = EmbeddingService(MockEmbeddingProvider())
    return _embedding_service
