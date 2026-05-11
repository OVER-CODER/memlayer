"""
OpenAI provider implementation.
"""

import time
from typing import Optional
from app.services.providers.base import (
    BaseLLMProvider,
    ProviderType,
    GenerationConfig,
    GenerationResult,
    ProviderFactory,
)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider (GPT-3.5, GPT-4, etc.)."""

    def __init__(
        self, api_key: Optional[str] = None, model_name: str = "gpt-3.5-turbo"
    ):
        super().__init__(api_key, model_name)
        self._validate_config()

        try:
            import openai

            openai.api_key = self.api_key
            self.openai = openai
        except ImportError:
            raise ImportError(
                "openai package not installed. Install with: pip install openai"
            )

    def _get_provider_type(self) -> ProviderType:
        """Return provider type."""
        return ProviderType.OPENAI

    def _validate_config(self):
        """Validate OpenAI configuration."""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not provided")
        if not self.model_name:
            raise ValueError("model_name is required")

    def generate(
        self, prompt: str, config: GenerationConfig = None, **kwargs
    ) -> GenerationResult:
        """Generate response from OpenAI."""
        if config is None:
            config = GenerationConfig()

        start_time = time.time()

        try:
            response = self.openai.ChatCompletion.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=config.temperature,
                top_p=config.top_p,
                max_tokens=config.max_tokens,
                **kwargs,
            )

            latency_ms = (time.time() - start_time) * 1000

            text = response.choices[0].message.content

            # Use actual token counts from OpenAI
            tokens_used = response.usage.completion_tokens
            tokens_input = response.usage.prompt_tokens

            return GenerationResult(
                text=text,
                provider="openai",
                model=self.model_name,
                tokens_used=tokens_used,
                tokens_estimated=tokens_input + tokens_used,
                latency_ms=latency_ms,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "total_tokens": response.usage.total_tokens,
                },
            )

        except Exception as e:
            raise RuntimeError(f"OpenAI generation failed: {str(e)}")

    def format_context_prompt(
        self, context: str, query: str, system_prompt: Optional[str] = None
    ) -> str:
        """Format prompt for OpenAI."""
        default_system = (
            "You are a helpful AI assistant with access to persistent semantic memory. "
            "Use the provided context to give accurate, personalized responses."
        )

        system = system_prompt or default_system

        return f"""{system}

## Context

{context}

## Query

{query}

## Response"""

    def get_token_estimate(self, text: str) -> int:
        """Estimate tokens using OpenAI's approximation."""
        # OpenAI uses ~1.3 tokens per word on average
        word_count = len(text.split())
        return max(1, int(word_count * 1.3))

    def supports_streaming(self) -> bool:
        """OpenAI supports streaming."""
        return True

    def get_max_tokens(self) -> int:
        """Get maximum tokens for OpenAI model."""
        # GPT-4: 8k, GPT-4-32k: 32k, GPT-3.5: 4k
        if "32k" in self.model_name:
            return 32000
        elif "gpt-4" in self.model_name:
            return 8192
        else:
            return 4096


# Register the provider
ProviderFactory.register(ProviderType.OPENAI, OpenAIProvider)
