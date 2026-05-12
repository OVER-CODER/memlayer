"""Delegation Runtime for Phase 7 Shared Agent Runtime.

Provides deterministic task handoff, semantic state delegation,
replayable coordination, and structured runtime transitions between agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json
import uuid

from app.agent_runtime.agents import AgentType, AgentExecutionResult


@dataclass
class DelegationRequest:
    """A structured delegation from one agent to another."""

    delegation_id: str
    source_agent_id: str
    source_agent_type: AgentType
    target_agent_type: AgentType
    workspace_id: str
    reason: str
    semantic_context_summary: str = ""
    source_projection_checksum: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delegation_id": self.delegation_id,
            "source_agent_id": self.source_agent_id,
            "source_agent_type": self.source_agent_type.value,
            "target_agent_type": self.target_agent_type.value,
            "workspace_id": self.workspace_id,
            "reason": self.reason,
            "semantic_context_summary": self.semantic_context_summary[:200],
            "source_projection_checksum": self.source_projection_checksum,
            "constraints": self.constraints,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class DelegationResult:
    """Outcome of a completed delegation."""

    delegation_id: str
    source_agent_id: str
    target_agent_id: str
    target_agent_type: AgentType
    workspace_id: str
    completed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Semantic continuity
    source_projection_checksum: str = ""
    target_projection_checksum: str = ""
    semantic_continuity_score: float = 0.0

    # Execution metrics
    target_execution_result: Optional[AgentExecutionResult] = None
    tokens_saved_by_delegation: int = 0
    delegation_duration_ms: float = 0.0

    # Status
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delegation_id": self.delegation_id,
            "source_agent_id": self.source_agent_id,
            "target_agent_id": self.target_agent_id,
            "target_agent_type": self.target_agent_type.value,
            "workspace_id": self.workspace_id,
            "completed_at": self.completed_at.isoformat(),
            "source_projection_checksum": self.source_projection_checksum,
            "target_projection_checksum": self.target_projection_checksum,
            "semantic_continuity_score": self.semantic_continuity_score,
            "tokens_saved_by_delegation": self.tokens_saved_by_delegation,
            "delegation_duration_ms": self.delegation_duration_ms,
            "success": self.success,
            "error_message": self.error_message,
        }


@dataclass
class DelegationChain:
    """A sequence of delegations forming a coordination chain."""

    chain_id: str
    workspace_id: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    delegations: List[DelegationResult] = field(default_factory=list)
    total_tokens_saved: int = 0
    avg_semantic_continuity: float = 0.0

    def add(self, result: DelegationResult) -> None:
        self.delegations.append(result)
        self.total_tokens_saved = sum(d.tokens_saved_by_delegation for d in self.delegations)
        continuities = [d.semantic_continuity_score for d in self.delegations if d.success]
        self.avg_semantic_continuity = sum(continuities) / len(continuities) if continuities else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "workspace_id": self.workspace_id,
            "started_at": self.started_at.isoformat(),
            "chain_length": len(self.delegations),
            "total_tokens_saved": self.total_tokens_saved,
            "avg_semantic_continuity": self.avg_semantic_continuity,
            "delegations": [d.to_dict() for d in self.delegations],
        }


class DelegationRuntime:
    """Manages deterministic, replayable task delegations between agents.

    Tracks delegation chains, semantic continuity across handoffs,
    and token savings from shared cognition.
    """

    def __init__(self):
        self._pending: Dict[str, DelegationRequest] = {}
        self._results: List[DelegationResult] = []
        self._chains: Dict[str, DelegationChain] = {}

    def create_delegation(
        self,
        source_agent_id: str,
        source_agent_type: AgentType,
        target_agent_type: AgentType,
        workspace_id: str,
        reason: str,
        source_projection_checksum: str = "",
        semantic_context_summary: str = "",
        chain_id: Optional[str] = None,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> DelegationRequest:
        """Create a new delegation request."""
        delegation_id = f"deleg-{uuid.uuid4().hex[:12]}"

        request = DelegationRequest(
            delegation_id=delegation_id,
            source_agent_id=source_agent_id,
            source_agent_type=source_agent_type,
            target_agent_type=target_agent_type,
            workspace_id=workspace_id,
            reason=reason,
            source_projection_checksum=source_projection_checksum,
            semantic_context_summary=semantic_context_summary,
            constraints=constraints or {},
        )
        self._pending[delegation_id] = request

        # Ensure chain exists
        resolved_chain_id = chain_id or f"chain-{workspace_id}"
        if resolved_chain_id not in self._chains:
            self._chains[resolved_chain_id] = DelegationChain(
                chain_id=resolved_chain_id,
                workspace_id=workspace_id,
            )

        return request

    def complete_delegation(
        self,
        delegation_id: str,
        target_agent_id: str,
        target_projection_checksum: str = "",
        execution_result: Optional[AgentExecutionResult] = None,
        semantic_continuity_score: float = 0.0,
        tokens_saved: int = 0,
        duration_ms: float = 0.0,
        success: bool = True,
        error_message: Optional[str] = None,
        chain_id: Optional[str] = None,
    ) -> DelegationResult:
        """Record the completion of a delegation."""
        request = self._pending.pop(delegation_id, None)

        result = DelegationResult(
            delegation_id=delegation_id,
            source_agent_id=request.source_agent_id if request else "unknown",
            target_agent_id=target_agent_id,
            target_agent_type=request.target_agent_type if request else AgentType.RESEARCH,
            workspace_id=request.workspace_id if request else "",
            source_projection_checksum=request.source_projection_checksum if request else "",
            target_projection_checksum=target_projection_checksum,
            semantic_continuity_score=semantic_continuity_score,
            target_execution_result=execution_result,
            tokens_saved_by_delegation=tokens_saved,
            delegation_duration_ms=duration_ms,
            success=success,
            error_message=error_message,
        )
        self._results.append(result)

        # Attach to chain
        resolved_chain_id = chain_id or (f"chain-{request.workspace_id}" if request else None)
        if resolved_chain_id and resolved_chain_id in self._chains:
            self._chains[resolved_chain_id].add(result)

        return result

    def get_delegation_statistics(self) -> Dict[str, Any]:
        """Get delegation runtime statistics."""
        if not self._results:
            return {"message": "No delegations completed"}

        total = len(self._results)
        successful = sum(1 for r in self._results if r.success)
        continuities = [r.semantic_continuity_score for r in self._results if r.success]

        return {
            "total_delegations": total,
            "successful_delegations": successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "total_tokens_saved": sum(r.tokens_saved_by_delegation for r in self._results),
            "avg_semantic_continuity": sum(continuities) / len(continuities) if continuities else 0.0,
            "avg_delegation_duration_ms": sum(r.delegation_duration_ms for r in self._results) / total,
            "pending_delegations": len(self._pending),
            "total_chains": len(self._chains),
        }

    def get_chain(self, chain_id: str) -> Optional[DelegationChain]:
        return self._chains.get(chain_id)

    def get_all_chains(self) -> List[DelegationChain]:
        return list(self._chains.values())

    def export_delegation_history(self, output_file: str) -> str:
        """Export delegation history to JSON."""
        payload = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "statistics": self.get_delegation_statistics(),
            "chains": {cid: c.to_dict() for cid, c in self._chains.items()},
            "recent_results": [r.to_dict() for r in self._results[-200:]],
        }
        with open(output_file, "w") as f:
            json.dump(payload, f, indent=2)
        return output_file
