"""View definition framework for Phase 6 View Engine Compiler."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Any


class ViewType(str, Enum):
    """Supported runtime view projections."""

    RESEARCH = "research"
    DRAFTER = "drafter"
    TOOL_AGENT = "tool_agent"
    CRITIC = "critic"


@dataclass
class ViewSemanticObjectives:
    """Semantic objective profile for a view."""

    semantic_breadth: float = 0.5
    citation_traceability: float = 0.5
    narrative_continuity: float = 0.5
    actionability: float = 0.5
    contradiction_focus: float = 0.5
    determinism_bias: float = 0.5


@dataclass
class ViewOptimizationPriorities:
    """Optimization preferences for view compilation."""

    quality_weight: float = 0.35
    continuity_weight: float = 0.25
    token_efficiency_weight: float = 0.20
    provider_fit_weight: float = 0.20


@dataclass
class ViewTokenPreferences:
    """Token distribution preferences for projection shaping."""

    reasoning_context_ratio: float = 0.30
    semantic_memories_ratio: float = 0.40
    workspace_summary_ratio: float = 0.20
    metadata_ratio: float = 0.10


@dataclass
class ProviderViewProfile:
    """Provider-specific shaping modifiers for a view."""

    quality_bias: float = 1.0
    continuity_bias: float = 1.0
    compression_bias: float = 1.0
    contradiction_bias: float = 1.0


@dataclass
class ViewDefinition:
    """Complete view definition used by compiler."""

    view_type: ViewType
    name: str
    description: str
    semantic_objectives: ViewSemanticObjectives
    optimization_priorities: ViewOptimizationPriorities
    token_preferences: ViewTokenPreferences
    base_token_budget_ratio: float = 1.0
    memory_selection_ratio: float = 0.8
    compression_preference: str = "balanced"
    provider_profiles: Dict[str, ProviderViewProfile] = field(default_factory=dict)

    def resolve_provider_profile(self, provider: str) -> ProviderViewProfile:
        """Return provider profile, falling back to neutral profile."""
        return self.provider_profiles.get(provider, ProviderViewProfile())


class ViewDefinitionFramework:
    """Registry and resolver for view definitions."""

    def __init__(self):
        self._definitions: Dict[ViewType, ViewDefinition] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register built-in foundational views."""
        self._definitions[ViewType.RESEARCH] = ViewDefinition(
            view_type=ViewType.RESEARCH,
            name="Research View",
            description=(
                "Optimized for semantic breadth, citations, historical continuity, "
                "and source traceability."
            ),
            semantic_objectives=ViewSemanticObjectives(
                semantic_breadth=0.95,
                citation_traceability=0.95,
                narrative_continuity=0.65,
                actionability=0.40,
                contradiction_focus=0.55,
                determinism_bias=0.85,
            ),
            optimization_priorities=ViewOptimizationPriorities(
                quality_weight=0.40,
                continuity_weight=0.25,
                token_efficiency_weight=0.15,
                provider_fit_weight=0.20,
            ),
            token_preferences=ViewTokenPreferences(
                reasoning_context_ratio=0.35,
                semantic_memories_ratio=0.45,
                workspace_summary_ratio=0.15,
                metadata_ratio=0.05,
            ),
            base_token_budget_ratio=1.15,
            memory_selection_ratio=0.95,
            compression_preference="conservative",
            provider_profiles={
                "claude": ProviderViewProfile(
                    quality_bias=1.15,
                    continuity_bias=1.20,
                    compression_bias=0.90,
                    contradiction_bias=1.00,
                ),
                "openai": ProviderViewProfile(
                    quality_bias=1.05,
                    continuity_bias=1.00,
                    compression_bias=1.00,
                    contradiction_bias=1.00,
                ),
                "gemini": ProviderViewProfile(
                    quality_bias=1.00,
                    continuity_bias=0.95,
                    compression_bias=1.05,
                    contradiction_bias=1.05,
                ),
            },
        )

        self._definitions[ViewType.DRAFTER] = ViewDefinition(
            view_type=ViewType.DRAFTER,
            name="Drafter View",
            description=(
                "Optimized for narrative continuity, writing coherence, "
                "structured context flow, and concise reasoning."
            ),
            semantic_objectives=ViewSemanticObjectives(
                semantic_breadth=0.70,
                citation_traceability=0.55,
                narrative_continuity=0.95,
                actionability=0.55,
                contradiction_focus=0.45,
                determinism_bias=0.80,
            ),
            optimization_priorities=ViewOptimizationPriorities(
                quality_weight=0.35,
                continuity_weight=0.35,
                token_efficiency_weight=0.20,
                provider_fit_weight=0.10,
            ),
            token_preferences=ViewTokenPreferences(
                reasoning_context_ratio=0.30,
                semantic_memories_ratio=0.35,
                workspace_summary_ratio=0.25,
                metadata_ratio=0.10,
            ),
            base_token_budget_ratio=0.95,
            memory_selection_ratio=0.75,
            compression_preference="balanced",
            provider_profiles={
                "claude": ProviderViewProfile(quality_bias=1.08, continuity_bias=1.15, compression_bias=0.95),
                "openai": ProviderViewProfile(quality_bias=1.02, continuity_bias=1.05, compression_bias=1.00),
                "gemini": ProviderViewProfile(quality_bias=0.98, continuity_bias=1.00, compression_bias=1.05),
            },
        )

        self._definitions[ViewType.TOOL_AGENT] = ViewDefinition(
            view_type=ViewType.TOOL_AGENT,
            name="Tool Agent View",
            description=(
                "Optimized for actionable state, deterministic context, "
                "operational data, and minimal ambiguity."
            ),
            semantic_objectives=ViewSemanticObjectives(
                semantic_breadth=0.55,
                citation_traceability=0.60,
                narrative_continuity=0.45,
                actionability=0.98,
                contradiction_focus=0.60,
                determinism_bias=0.98,
            ),
            optimization_priorities=ViewOptimizationPriorities(
                quality_weight=0.30,
                continuity_weight=0.15,
                token_efficiency_weight=0.30,
                provider_fit_weight=0.25,
            ),
            token_preferences=ViewTokenPreferences(
                reasoning_context_ratio=0.25,
                semantic_memories_ratio=0.30,
                workspace_summary_ratio=0.20,
                metadata_ratio=0.25,
            ),
            base_token_budget_ratio=0.85,
            memory_selection_ratio=0.65,
            compression_preference="aggressive",
            provider_profiles={
                "claude": ProviderViewProfile(quality_bias=1.00, continuity_bias=0.95, compression_bias=1.00),
                "openai": ProviderViewProfile(quality_bias=1.05, continuity_bias=0.95, compression_bias=1.15),
                "gemini": ProviderViewProfile(quality_bias=0.95, continuity_bias=0.90, compression_bias=1.10),
            },
        )

        self._definitions[ViewType.CRITIC] = ViewDefinition(
            view_type=ViewType.CRITIC,
            name="Critic View",
            description=(
                "Optimized for contradiction detection, reasoning gap discovery, "
                "semantic inconsistency analysis, and missing context identification."
            ),
            semantic_objectives=ViewSemanticObjectives(
                semantic_breadth=0.75,
                citation_traceability=0.70,
                narrative_continuity=0.60,
                actionability=0.50,
                contradiction_focus=1.00,
                determinism_bias=0.90,
            ),
            optimization_priorities=ViewOptimizationPriorities(
                quality_weight=0.35,
                continuity_weight=0.25,
                token_efficiency_weight=0.15,
                provider_fit_weight=0.25,
            ),
            token_preferences=ViewTokenPreferences(
                reasoning_context_ratio=0.40,
                semantic_memories_ratio=0.35,
                workspace_summary_ratio=0.15,
                metadata_ratio=0.10,
            ),
            base_token_budget_ratio=1.05,
            memory_selection_ratio=0.85,
            compression_preference="balanced",
            provider_profiles={
                "claude": ProviderViewProfile(quality_bias=1.08, continuity_bias=1.05, compression_bias=0.95, contradiction_bias=1.10),
                "openai": ProviderViewProfile(quality_bias=1.00, continuity_bias=1.00, compression_bias=1.00, contradiction_bias=1.08),
                "gemini": ProviderViewProfile(quality_bias=1.02, continuity_bias=0.98, compression_bias=1.00, contradiction_bias=1.15),
            },
        )

    def get_view_definition(self, view_type: ViewType) -> ViewDefinition:
        """Get a view definition by type."""
        if view_type not in self._definitions:
            raise ValueError(f"Unsupported view type: {view_type}")
        return self._definitions[view_type]

    def register_view_definition(self, definition: ViewDefinition) -> None:
        """Register or replace a view definition."""
        self._definitions[definition.view_type] = definition

    def update_view_definition(
        self,
        view_type: ViewType,
        updates: Dict[str, Any],
    ) -> ViewDefinition:
        """Apply partial updates to a view definition."""
        current = self.get_view_definition(view_type)
        payload = {
            "view_type": current.view_type,
            "name": current.name,
            "description": current.description,
            "semantic_objectives": current.semantic_objectives,
            "optimization_priorities": current.optimization_priorities,
            "token_preferences": current.token_preferences,
            "base_token_budget_ratio": current.base_token_budget_ratio,
            "memory_selection_ratio": current.memory_selection_ratio,
            "compression_preference": current.compression_preference,
            "provider_profiles": current.provider_profiles,
        }
        payload.update(updates)
        updated = ViewDefinition(**payload)
        self.register_view_definition(updated)
        return updated

    def list_definitions(self) -> Dict[str, Dict[str, Any]]:
        """List available definitions in dictionary form."""
        output: Dict[str, Dict[str, Any]] = {}
        for view_type, definition in self._definitions.items():
            output[view_type.value] = {
                "name": definition.name,
                "description": definition.description,
                "compression_preference": definition.compression_preference,
                "token_budget_ratio": definition.base_token_budget_ratio,
                "memory_selection_ratio": definition.memory_selection_ratio,
            }
        return output
