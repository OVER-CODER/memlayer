"""Agent type definitions for Phase 7 Shared Agent Runtime.

Defines the foundational agent types that consume shared compiled
semantic projections. Agents do NOT independently rebuild context —
they consume views produced by the cognition substrate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentType(str, Enum):
    """Foundational runtime agent types."""

    RESEARCH = "research"
    DRAFTER = "drafter"
    TOOL_AGENT = "tool_agent"
    CRITIC = "critic"


# Maps each agent type to the view it consumes
AGENT_VIEW_MAP: Dict[str, str] = {
    AgentType.RESEARCH: "research",
    AgentType.DRAFTER: "drafter",
    AgentType.TOOL_AGENT: "tool_agent",
    AgentType.CRITIC: "critic",
}


@dataclass
class AgentCapabilities:
    """Declarative capability profile for an agent type."""

    primary_objective: str
    semantic_strengths: List[str]
    output_type: str
    preferred_providers: List[str] = field(default_factory=lambda: ["claude", "openai", "gemini"])
    max_token_budget_ratio: float = 1.0
    supports_delegation: bool = True


# Built-in capability profiles
AGENT_CAPABILITIES: Dict[AgentType, AgentCapabilities] = {
    AgentType.RESEARCH: AgentCapabilities(
        primary_objective="evidence gathering and semantic breadth analysis",
        semantic_strengths=["citation_traceability", "semantic_breadth", "factual_continuity"],
        output_type="structured_evidence",
        max_token_budget_ratio=1.15,
    ),
    AgentType.DRAFTER: AgentCapabilities(
        primary_objective="narrative synthesis and structured output generation",
        semantic_strengths=["narrative_continuity", "semantic_coherence", "drafting_flow"],
        output_type="structured_draft",
        max_token_budget_ratio=0.95,
    ),
    AgentType.TOOL_AGENT: AgentCapabilities(
        primary_objective="deterministic task execution and operational planning",
        semantic_strengths=["actionability", "determinism", "operational_state"],
        output_type="execution_plan",
        max_token_budget_ratio=0.85,
    ),
    AgentType.CRITIC: AgentCapabilities(
        primary_objective="contradiction detection and reasoning evaluation",
        semantic_strengths=["contradiction_focus", "reasoning_evaluation", "consistency_analysis"],
        output_type="critique_report",
        max_token_budget_ratio=1.05,
    ),
}


@dataclass
class AgentExecutionResult:
    """Result of a single agent execution against a compiled view."""

    agent_id: str
    agent_type: AgentType
    execution_id: str
    view_id: str
    provider: str
    workspace_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Semantic output
    output_content: str = ""
    output_type: str = ""
    output_metadata: Dict[str, Any] = field(default_factory=dict)

    # Cognition metrics
    tokens_consumed: int = 0
    tokens_from_shared_view: int = 0
    tokens_saved_vs_independent: int = 0
    semantic_reuse_ratio: float = 0.0
    projection_checksum: str = ""

    # Quality
    quality_score: float = 0.0
    semantic_continuity: float = 0.0

    # Execution
    duration_ms: float = 0.0
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "execution_id": self.execution_id,
            "view_id": self.view_id,
            "provider": self.provider,
            "workspace_id": self.workspace_id,
            "timestamp": self.timestamp.isoformat(),
            "output_content": self.output_content[:200] + "..." if len(self.output_content) > 200 else self.output_content,
            "output_type": self.output_type,
            "tokens_consumed": self.tokens_consumed,
            "tokens_from_shared_view": self.tokens_from_shared_view,
            "tokens_saved_vs_independent": self.tokens_saved_vs_independent,
            "semantic_reuse_ratio": self.semantic_reuse_ratio,
            "projection_checksum": self.projection_checksum,
            "quality_score": self.quality_score,
            "semantic_continuity": self.semantic_continuity,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error_message": self.error_message,
        }
