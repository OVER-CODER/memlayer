"""
Mistral Embedding Provider - Phase D1.9
Uses Mistral's embedding models for real semantic embeddings.
"""

import os
import requests
from typing import List, Optional
from app.embeddings.base import IEmbeddingProvider, EmbeddingMetadata


class MistralEmbeddingProvider(IEmbeddingProvider):
    """Mistral embedding provider using mistral-embed model."""

    def __init__(self, api_key: str = None, model: str = "mistral-embed"):
        self._api_key = (
            api_key or os.getenv("MISTRAL_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        )
        self._model = model
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

def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if not self._api_key:
            raise RuntimeError("Mistral API key not available")

        try:
            response = requests.post(
                'https://api.mistral.ai/v1/embeddings',
                headers={
                    'Authorization': f'Bearer {self._api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': self._model,
                    'input': text  # Single input, not "inputs"
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json()['data'][0]['embedding']
            else:
                raise Exception(f"Mistral API error: {response.status_code} - {response.text}")
        except Exception as e:
            raise RuntimeError(f"Mistral embedding failed: {e}")

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not self._api_key:
            raise RuntimeError("Mistral API key not available")

        try:
            response = requests.post(
                'https://api.mistral.ai/v1/embeddings',
                headers={
                    'Authorization': f'Bearer {self._api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': self._model,
                    'inputs': texts  # Batch uses "inputs"
                },
                timeout=60
            )
            if response.status_code == 200:
                return [item['embedding'] for item in response.json()['data']]
            else:
                raise Exception(f"Mistral API error: {response.status_code}")
        except Exception as e:
            raise RuntimeError(f"Mistral batch embedding failed: {e}")

def is_available(self) -> bool:
        """Check if provider is available."""
        if not self._api_key:
            return False
        # Quick health check - use "input" not "inputs"
        try:
            response = requests.post(
                'https://api.mistral.ai/v1/embeddings',
                headers={
                    'Authorization': f'Bearer {self._api_key}',
                    'Content-Type': 'application/json'
                },
                json={'model': self._model, 'input': 'test'},
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
        # Quick health check
        try:
            response = requests.post(
                "https://api.mistral.ai/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": self._model, "inputs": ["test"]},
                timeout=5,
            )
            return response.status_code == 200
        except:
            return False
