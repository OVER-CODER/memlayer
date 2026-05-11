"""
Gemini provider implementation.
"""

import time
from typing import Optional
import google.generativeai as genai
from app.services.providers.base import (
    BaseLLMProvider,
    ProviderType,
    GenerationConfig,
    GenerationResult,
    ProviderFactory,
)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-pro"):
        super().__init__(api_key, model_name)
        self._validate_config()
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def _get_provider_type(self) -> ProviderType:
        """Return provider type."""
        return ProviderType.GEMINI

    def _validate_config(self):
        """Validate Gemini configuration."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not provided")
        if not self.model_name:
            raise ValueError("model_name is required")

    def generate(
        self, prompt: str, config: GenerationConfig = None, **kwargs
    ) -> GenerationResult:
        """Generate response from Gemini."""
        if config is None:
            config = GenerationConfig()

        start_time = time.time()

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=config.temperature,
                    top_p=config.top_p,
                    top_k=config.top_k,
                    max_output_tokens=config.max_tokens,
                ),
                safety_settings=kwargs.get("safety_settings", []),
            )

            latency_ms = (time.time() - start_time) * 1000

            # Estimate tokens used
            tokens_used = self._estimate_tokens(response.text)
            tokens_estimated = self._estimate_tokens(prompt) + tokens_used

            return GenerationResult(
                text=response.text,
                provider="gemini",
                model=self.model_name,
                tokens_used=tokens_used,
                tokens_estimated=tokens_estimated,
                latency_ms=latency_ms,
                metadata={
                    "finish_reason": getattr(response, "finish_reason", "STOP"),
                },
            )

        except Exception as e:
            raise RuntimeError(f"Gemini generation failed: {str(e)}")

    def format_context_prompt(
        self, context: str, query: str, system_prompt: Optional[str] = None
    ) -> str:
        """Format prompt for Gemini."""
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
        """Estimate tokens (rough: ~4 chars per token)."""
        return max(1, len(text) // 4)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return self.get_token_estimate(text)

    def supports_streaming(self) -> bool:
        """Gemini supports streaming."""
        return True

    def get_max_tokens(self) -> int:
        """Get maximum tokens for Gemini Pro."""
        # Gemini Pro: 32k context, 8k output
        if "ultra" in self.model_name.lower():
            return 8192
        return 8192


# Register the provider
ProviderFactory.register(ProviderType.GEMINI, GeminiProvider)
