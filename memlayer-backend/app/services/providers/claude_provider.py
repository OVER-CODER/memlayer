"""
Claude (Anthropic) provider implementation.
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


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude API provider."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "claude-2"):
        super().__init__(api_key, model_name)
        self._validate_config()

        try:
            import anthropic

            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Install with: pip install anthropic"
            )

    def _get_provider_type(self) -> ProviderType:
        """Return provider type."""
        return ProviderType.CLAUDE

    def _validate_config(self):
        """Validate Claude configuration."""
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not provided")
        if not self.model_name:
            raise ValueError("model_name is required")

    def generate(
        self, prompt: str, config: GenerationConfig = None, **kwargs
    ) -> GenerationResult:
        """Generate response from Claude."""
        if config is None:
            config = GenerationConfig()

        start_time = time.time()

        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=config.max_tokens,
                messages=[{"role": "user", "content": prompt}],
                temperature=config.temperature,
                **kwargs,
            )

            latency_ms = (time.time() - start_time) * 1000

            text = response.content[0].text

            # Estimate tokens (Claude uses similar token counting)
            tokens_used = self.get_token_estimate(text)
            tokens_estimated = self.get_token_estimate(prompt) + tokens_used

            return GenerationResult(
                text=text,
                provider="claude",
                model=self.model_name,
                tokens_used=tokens_used,
                tokens_estimated=tokens_estimated,
                latency_ms=latency_ms,
                metadata={
                    "stop_reason": response.stop_reason,
                    "usage": {
                        "input_tokens": getattr(response.usage, "input_tokens", 0),
                        "output_tokens": getattr(response.usage, "output_tokens", 0),
                    },
                },
            )

        except Exception as e:
            raise RuntimeError(f"Claude generation failed: {str(e)}")

    def format_context_prompt(
        self, context: str, query: str, system_prompt: Optional[str] = None
    ) -> str:
        """Format prompt for Claude.

        Claude's best practices recommend clear role-playing and explicit formatting.
        """
        default_system = (
            "You are a helpful AI assistant with access to persistent semantic memory. "
            "Use the provided context to give accurate, personalized responses. "
            "Be concise and clear in your responses."
        )

        system = system_prompt or default_system

        return f"""{system}

## Context

{context}

## User Query

{query}

## Your Response:"""

    def get_token_estimate(self, text: str) -> int:
        """Estimate tokens for Claude.

        Claude uses similar token counting to OpenAI (roughly 1 token per 3-4 chars).
        """
        return max(1, len(text) // 4)

    def supports_streaming(self) -> bool:
        """Claude supports streaming."""
        return True

    def get_max_tokens(self) -> int:
        """Get maximum tokens for Claude model."""
        # Claude 2: 100k context, 4k output
        # Claude 3: varies by variant
        if "claude-3" in self.model_name:
            if "opus" in self.model_name:
                return 4096
            elif "sonnet" in self.model_name:
                return 4096
            else:  # haiku
                return 4096
        elif "claude-2" in self.model_name:
            return 4096
        else:
            return 2048


# Register the provider
ProviderFactory.register(ProviderType.CLAUDE, ClaudeProvider)
