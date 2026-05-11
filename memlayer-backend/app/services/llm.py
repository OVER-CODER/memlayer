"""
LLM service layer - Model-agnostic interface for LLM operations.

This service uses the new provider factory architecture to support
multiple LLM providers (Gemini, OpenAI, Claude) without conditional logic.
"""

from typing import Optional, List, Dict
from app.services.providers import (
    ProviderFactory,
    ProviderType,
    BaseLLMProvider,
    GenerationConfig,
    GenerationResult,
)
from app.core.config import settings


class LLMService:
    """Service for LLM interactions with pluggable providers.

    This service:
    - Manages provider instantiation via ProviderFactory
    - Remains completely provider-agnostic
    - Returns structured GenerationResult objects
    - Tracks generation metadata for debugging and optimization
    """

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        provider_type: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        """Initialize LLM service with a provider.

        Args:
            provider: Existing provider instance (optional)
            provider_type: Type of provider to create (gemini, openai, claude)
            model_name: Model name to use
        """
        if provider:
            self.provider = provider
        elif provider_type:
            # Get API key from settings based on provider type
            api_key = self._get_api_key_for_provider(provider_type)
            self.provider = ProviderFactory.create(
                provider_type=provider_type,
                api_key=api_key,
                model_name=model_name,
            )
        else:
            # Use default provider from settings
            default_provider = settings.default_provider or "gemini"
            api_key = self._get_api_key_for_provider(default_provider)
            model = settings.default_model or self._get_default_model(default_provider)
            self.provider = ProviderFactory.create(
                provider_type=default_provider,
                api_key=api_key,
                model_name=model,
            )

    def _get_api_key_for_provider(self, provider_type: str) -> str:
        """Get API key from settings for provider type."""
        provider_lower = provider_type.lower()

        if provider_lower == "gemini":
            api_key = settings.gemini_api_key
        elif provider_lower == "openai":
            api_key = settings.openai_api_key
        elif provider_lower == "claude":
            api_key = settings.anthropic_api_key
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")

        if not api_key:
            raise ValueError(f"No API key configured for provider: {provider_type}")

        return api_key

    def _get_default_model(self, provider_type: str) -> str:
        """Get default model name for provider type."""
        provider_lower = provider_type.lower()

        if provider_lower == "gemini":
            return "gemini-pro"
        elif provider_lower == "openai":
            return "gpt-3.5-turbo"
        elif provider_lower == "claude":
            return "claude-2"
        else:
            return None

    def generate(
        self, prompt: str, config: Optional[GenerationConfig] = None, **kwargs
    ) -> GenerationResult:
        """Generate a response from the LLM.

        Args:
            prompt: The input prompt
            config: Generation configuration
            **kwargs: Provider-specific arguments

        Returns:
            GenerationResult with text and metadata
        """
        return self.provider.generate(prompt, config, **kwargs)

    def generate_with_context(
        self,
        context: str,
        query: str,
        config: Optional[GenerationConfig] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> GenerationResult:
        """Generate response with structured context.

        Args:
            context: Structured context information
            query: User query
            config: Generation configuration
            system_prompt: Optional system prompt override
            **kwargs: Provider-specific arguments

        Returns:
            GenerationResult with text and metadata
        """
        return self.provider.generate_with_context(
            context=context,
            query=query,
            config=config,
            system_prompt=system_prompt,
            **kwargs,
        )

    def extract_memory_objects(self, response: str) -> List[Dict]:
        """Extract potential memory objects from the response.

        This is a simple implementation that identifies important facts.
        In a production system, this could use NER or structured extraction.

        Args:
            response: The LLM response text

        Returns:
            List of extracted memory objects
        """
        # Flag responses as potential memories for later processing
        return [
            {
                "type": "response",
                "content": response,
                "importance": 0.7,
            }
        ]

    def get_provider_info(self) -> Dict:
        """Get information about the current provider.

        Returns:
            Dictionary with provider information
        """
        return {
            "provider": self.provider.provider_type.value,
            "model": self.provider.model_name,
            "supports_streaming": self.provider.supports_streaming(),
            "max_tokens": self.provider.get_max_tokens(),
        }

    def switch_provider(
        self,
        provider_type: str,
        model_name: Optional[str] = None,
    ) -> None:
        """Switch to a different provider at runtime.

        Args:
            provider_type: Type of provider (gemini, openai, claude)
            model_name: Optional model name override

        Raises:
            ValueError: If provider type is invalid or API key not configured
        """
        api_key = self._get_api_key_for_provider(provider_type)
        model = model_name or self._get_default_model(provider_type)

        self.provider = ProviderFactory.create(
            provider_type=provider_type,
            api_key=api_key,
            model_name=model,
        )


# Global LLM service instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the global LLM service.

    Returns:
        LLMService instance
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def set_llm_service(service: LLMService) -> None:
    """Set a custom LLM service instance.

    Useful for testing with mock providers.

    Args:
        service: LLMService instance to use
    """
    global _llm_service
    _llm_service = service
