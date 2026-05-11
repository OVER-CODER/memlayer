"""
Core provider abstraction layer.
Defines interfaces for all LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum


class ProviderType(Enum):
    """Supported LLM provider types."""

    GEMINI = "gemini"
    OPENAI = "openai"
    CLAUDE = "claude"


@dataclass
class GenerationConfig:
    """Configuration for generation parameters."""

    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    max_tokens: int = 2048


@dataclass
class GenerationResult:
    """Result from LLM generation."""

    text: str
    provider: str
    model: str
    tokens_used: int = 0
    tokens_estimated: int = 0
    latency_ms: float = 0.0
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers.

    Defines the interface that all providers must implement.
    Ensures model-agnostic usage throughout the system.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = None):
        """Initialize provider with API key and model name.

        Args:
            api_key: API key for the provider (if needed)
            model_name: Name of the model to use
        """
        self.api_key = api_key
        self.model_name = model_name
        self.provider_type = self._get_provider_type()

    @abstractmethod
    def _get_provider_type(self) -> ProviderType:
        """Return the provider type."""
        pass

    @abstractmethod
    def _validate_config(self):
        """Validate that provider is properly configured."""
        pass

    @abstractmethod
    def generate(
        self, prompt: str, config: GenerationConfig = None, **kwargs
    ) -> GenerationResult:
        """Generate a response from the LLM.

        Args:
            prompt: The input prompt
            config: Generation configuration
            **kwargs: Provider-specific arguments

        Returns:
            GenerationResult with text and metadata
        """
        pass

    @abstractmethod
    def format_context_prompt(
        self, context: str, query: str, system_prompt: Optional[str] = None
    ) -> str:
        """Format a prompt with context for the provider.

        Each provider may have different optimal prompt formatting.

        Args:
            context: Structured context information
            query: User query
            system_prompt: Optional system prompt override

        Returns:
            Formatted prompt ready for generation
        """
        pass

    @abstractmethod
    def get_token_estimate(self, text: str) -> int:
        """Estimate token count for text.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        pass

    @abstractmethod
    def supports_streaming(self) -> bool:
        """Check if provider supports streaming responses."""
        pass

    @abstractmethod
    def get_max_tokens(self) -> int:
        """Get maximum tokens supported by this model."""
        pass

    def generate_with_context(
        self,
        context: str,
        query: str,
        config: GenerationConfig = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> GenerationResult:
        """Generate response with structured context.

        Default implementation that can be overridden by providers.

        Args:
            context: Structured context
            query: User query
            config: Generation config
            system_prompt: Optional system prompt
            **kwargs: Provider-specific args

        Returns:
            GenerationResult
        """
        if config is None:
            config = GenerationConfig()

        prompt = self.format_context_prompt(context, query, system_prompt)
        return self.generate(prompt, config, **kwargs)


class ProviderFactory:
    """Factory for creating provider instances."""

    _providers = {}

    @classmethod
    def register(cls, provider_type: ProviderType, provider_class):
        """Register a provider class."""
        cls._providers[provider_type.value] = provider_class

    @classmethod
    def create(
        cls,
        provider_type: str,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> BaseLLMProvider:
        """Create a provider instance.

        Args:
            provider_type: Type of provider (gemini, openai, claude)
            api_key: API key for the provider
            model_name: Model name to use

        Returns:
            Provider instance

        Raises:
            ValueError: If provider type is not registered
        """
        if provider_type not in cls._providers:
            raise ValueError(
                f"Unknown provider type: {provider_type}. "
                f"Available: {list(cls._providers.keys())}"
            )

        provider_class = cls._providers[provider_type]
        return provider_class(api_key=api_key, model_name=model_name)

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available provider types."""
        return list(cls._providers.keys())
