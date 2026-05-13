"""
Gemini Embedding Provider - Phase D1.9
Uses Google's Gemini embeddings for real semantic embeddings.
"""

import os
from typing import List, Optional
from app.embeddings.base import IEmbeddingProvider, EmbeddingMetadata
from app.core.config import settings


class GeminiEmbeddingProvider(IEmbeddingProvider):
    """Google Gemini embedding provider using gemini-embedding-001."""

    def __init__(self, api_key: str = None, model: str = "gemini-embedding-001"):
        self._api_key = (
            api_key or settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        )
        self._model = model
        self._client = None
        self._dimension = 768  # Gemini embedding dimension

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def version(self) -> str:
        return "gemini-embedding-001-2024"

    def _get_client(self):
        """Lazy initialization of Gemini client."""
        if self._client is None and self._api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self._api_key)
                self._client = genai
            except Exception as e:
                print(f"Gemini client init error: {e}")
                return None
        return self._client

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        client = self._get_client()
        if not client:
            raise RuntimeError("Gemini client not available - no API key")

        try:
            result = client.embed_content(model=self._model, content=text)
            return result.embedding
        except Exception as e:
            print(f"Gemini embedding error: {e}")
            raise

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        client = self._get_client()
        if not client:
            raise RuntimeError("Gemini client not available - no API key")

        embeddings = []
        for text in texts:
            result = client.embed_content(model=self._model, content=text)
            embeddings.append(result.embedding)
        return embeddings

    def is_available(self) -> bool:
        """Check if provider is available."""
        return bool(self._api_key) and self._get_client() is not None
