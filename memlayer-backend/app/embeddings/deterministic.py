"""
Deterministic Embedding Provider - Phase D1.8
Reproducible hash-based embeddings for replay-safe operation.
"""

import hashlib
import re
from typing import List
import numpy as np
from app.embeddings.base import IEmbeddingProvider, EmbeddingMetadata
from app.core.config import settings


class DeterministicEmbeddingProvider(IEmbeddingProvider):
    """Deterministic hash-based provider for replay-safe operation."""

    def __init__(self, dimension: int = None):
        self._dimension = dimension or settings.embedding_dim

    @property
    def provider_name(self) -> str:
        return "deterministic"

    @property
    def model_name(self) -> str:
        return "hash-v1"

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def version(self) -> str:
        return "deterministic-v1-2024"

    def _tokenize(self, text: str) -> List[str]:
        """Clean and tokenize text."""
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        return text.split()

    def _get_deterministic_vector(self, text: str) -> List[float]:
        """Generate deterministic vector from text."""
        tokens = self._tokenize(text)
        if not tokens:
            return [0.0] * self._dimension

        vector = [0.0] * self._dimension
        tokens_per_dim = max(1, len(tokens))

        for i, token in enumerate(tokens):
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            dims_per_token = min(8, self._dimension // tokens_per_dim)

            for j in range(dims_per_token):
                idx = (i * dims_per_token + j) % self._dimension
                val = int(token_hash[j * 4 : j * 4 + 4], 16) / 65535.0
                vector[idx] = (vector[idx] + val) / 2

        # Add position-based features
        for i, token in enumerate(tokens):
            pos_hash = hashlib.sha256(f"{token}:{i}".encode()).hexdigest()
            idx = self._dimension - 1 - (i % 8)
            val = int(pos_hash[:4], 16) / 65535.0
            vector[idx] = (vector[idx] + val) / 2

        # Normalize
        norm = np.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector

    def embed_text(self, text: str) -> List[float]:
        """Generate deterministic embedding for text."""
        return self._get_deterministic_vector(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate deterministic embeddings for multiple texts."""
        return [self._get_deterministic_vector(t) for t in texts]

    def is_available(self) -> bool:
        """Always available."""
        return True
