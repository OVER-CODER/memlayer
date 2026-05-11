"""
Provider package - LLM provider implementations and factory.

This package contains all LLM provider implementations and the factory for creating them.
All providers are automatically registered when imported.
"""

# Import base classes and enums first
from app.services.providers.base import (
    BaseLLMProvider,
    ProviderType,
    GenerationConfig,
    GenerationResult,
    ProviderFactory,
)

# Import all provider implementations (they register themselves on import)
from app.services.providers.gemini_provider import GeminiProvider
from app.services.providers.openai_provider import OpenAIProvider
from app.services.providers.claude_provider import ClaudeProvider

__all__ = [
    "BaseLLMProvider",
    "ProviderType",
    "GenerationConfig",
    "GenerationResult",
    "ProviderFactory",
    "GeminiProvider",
    "OpenAIProvider",
    "ClaudeProvider",
]
