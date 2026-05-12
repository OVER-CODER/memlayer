"""Provider Adapter Layer for Phase 8.

Lightweight, runtime-focused adapters that normalize provider interactions
while preserving provider-aware optimization. Not a full abstraction
framework — just enough to expose deterministic provider interfaces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class ProviderCapabilities:
    """Capabilities and constraints of a provider."""

    name: str
    max_context_tokens: int
    supports_streaming: bool = False
    supports_function_calling: bool = False
    default_temperature: float = 0.0
    token_cost_per_1k_input: float = 0.0
    token_cost_per_1k_output: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "max_context_tokens": self.max_context_tokens,
            "supports_streaming": self.supports_streaming,
            "supports_function_calling": self.supports_function_calling,
            "default_temperature": self.default_temperature,
            "token_cost_per_1k_input": self.token_cost_per_1k_input,
            "token_cost_per_1k_output": self.token_cost_per_1k_output,
        }


# Canonical provider definitions
PROVIDER_REGISTRY: Dict[str, ProviderCapabilities] = {
    "claude": ProviderCapabilities(
        name="claude",
        max_context_tokens=200000,
        supports_streaming=True,
        supports_function_calling=True,
        default_temperature=0.0,
        token_cost_per_1k_input=0.003,
        token_cost_per_1k_output=0.015,
    ),
    "openai": ProviderCapabilities(
        name="openai",
        max_context_tokens=128000,
        supports_streaming=True,
        supports_function_calling=True,
        default_temperature=0.0,
        token_cost_per_1k_input=0.005,
        token_cost_per_1k_output=0.015,
    ),
    "gemini": ProviderCapabilities(
        name="gemini",
        max_context_tokens=1000000,
        supports_streaming=True,
        supports_function_calling=True,
        default_temperature=0.0,
        token_cost_per_1k_input=0.00035,
        token_cost_per_1k_output=0.0014,
    ),
}


class ProviderAdapter:
    """Runtime-focused provider adapter.

    Normalizes provider interactions for the SDK layer.
    Does NOT handle actual LLM API calls — that's the consumer's
    responsibility. This adapter manages provider-aware configuration,
    token budget optimization, and cost estimation.
    """

    def __init__(self, default_provider: str = "claude"):
        self._default = default_provider
        self._available = dict(PROVIDER_REGISTRY)

    @property
    def default_provider(self) -> str:
        return self._default

    def get_capabilities(self, provider: str) -> Optional[ProviderCapabilities]:
        return self._available.get(provider)

    def list_providers(self) -> List[str]:
        return list(self._available.keys())

    def get_all_capabilities(self) -> Dict[str, Dict[str, Any]]:
        return {name: caps.to_dict() for name, caps in self._available.items()}

    def validate_budget(self, provider: str, token_budget: int) -> Dict[str, Any]:
        """Validate a token budget against provider constraints."""
        caps = self._available.get(provider)
        if not caps:
            return {"valid": False, "reason": f"unknown_provider:{provider}"}

        if token_budget > caps.max_context_tokens:
            return {
                "valid": False,
                "reason": "exceeds_max_context",
                "max": caps.max_context_tokens,
                "requested": token_budget,
            }
        return {"valid": True, "provider": provider, "budget": token_budget}

    def estimate_cost(self, provider: str, input_tokens: int, output_tokens: int = 0) -> Dict[str, float]:
        """Estimate token cost for a provider."""
        caps = self._available.get(provider)
        if not caps:
            return {"input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0}

        input_cost = (input_tokens / 1000) * caps.token_cost_per_1k_input
        output_cost = (output_tokens / 1000) * caps.token_cost_per_1k_output
        return {
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(input_cost + output_cost, 6),
        }

    def optimal_provider_for_budget(self, token_budget: int) -> str:
        """Select the most cost-effective provider for a budget."""
        candidates = [
            (name, caps) for name, caps in self._available.items()
            if caps.max_context_tokens >= token_budget
        ]
        if not candidates:
            return self._default

        # Sort by input cost, deterministic tiebreak by name
        candidates.sort(key=lambda x: (x[1].token_cost_per_1k_input, x[0]))
        return candidates[0][0]
