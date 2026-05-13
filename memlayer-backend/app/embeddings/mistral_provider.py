"""
Mistral Embedding Provider - Phase D1.9
Uses Mistral's embedding models for real semantic embeddings.
"""

import os
from typing import List, Optional
from app.embeddings.base import IEmbeddingProvider, EmbeddingMetadata
from app.core.config import settings


class MistralEmbeddingProvider(IEmbeddingProvider):
    """Mistral embedding provider using mistral-embed model."""

    def __init__(self, api_key: str = None, model: str = "mistral-embed"):
        self._api_key = (
            api_key or os.getenv("MISTRAL_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        )
        self._model = model
        self._client = None
        self._dimension = 1024  # mistral-embed dimension

    @property
    def provider_name(self) -> str:
        return "mistral"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def version(self) -> str:
        return "mistral-embed-2024"

    def _get_client(self):
        """Lazy initialization of Mistral client."""
        if self._client is None and self._api_key:
            try:
                from mistralai import Mistral

                self._client = Mistral(api_key=self._api_key)
            except Exception as e:
                print(f"Mistral client init error: {e}")
                return None
        return self._client

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        client = self._get_client()
        if not client:
            raise RuntimeError("Mistral client not available - no API key")

        response = client.embeddings.create(model=self._model, inputs=[text])
        return response.data[0].embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        client = self._get_client()
        if not client:
            raise RuntimeError("Mistral client not available - no API key")

        response = client.embeddings.create(model=self._model, inputs=texts)
        return [item.embedding for item in response.data]

    def is_available(self) -> bool:
        """Check if provider is available."""
        return bool(self._api_key) and self._get_client() is not None
