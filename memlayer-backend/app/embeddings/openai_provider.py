"""
OpenAI Embedding Provider - Phase D1.8
Uses OpenAI's text-embedding-3-small for high-quality semantic embeddings.
"""

import os
from typing import List
from app.embeddings.base import IEmbeddingProvider, EmbeddingMetadata
from app.core.config import settings


class OpenAIEmbeddingProvider(IEmbeddingProvider):
    """OpenAI text-embedding-3-small provider."""

    def __init__(self, api_key: str = None, model: str = "text-embedding-3-small"):
        self._api_key = (
            api_key or settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        )
        self._model = model
        self._client = None
        self._dimension = 1536  # text-embedding-3-small dimension

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def version(self) -> str:
        return "3-small-2024-01"

    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None and self._api_key:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=self._api_key)
            except Exception:
                return None
        return self._client

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        client = self._get_client()
        if not client:
            raise RuntimeError("OpenAI client not available - no API key")

        response = client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        client = self._get_client()
        if not client:
            raise RuntimeError("OpenAI client not available - no API key")

        response = client.embeddings.create(
            model=self._model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def is_available(self) -> bool:
        """Check if provider is available."""
        return bool(self._api_key)
