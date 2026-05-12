"""Agent State Registry for Phase 7 Shared Agent Runtime.

Tracks agent lifecycle, semantic state access, view subscriptions,
execution timelines, and coordination state. All state is deterministic
and replay-compatible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
import json
import uuid

from app.agent_runtime.agents import AgentType, AgentCapabilities, AGENT_CAPABILITIES


@dataclass
class AgentRegistration:
    """Registered agent instance."""

    agent_id: str
    agent_type: AgentType
    capabilities: AgentCapabilities
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "idle"  # idle, executing, delegating, completed, error
    total_executions: int = 0
    total_tokens_consumed: int = 0
    total_tokens_saved: int = 0
    last_execution_at: Optional[datetime] = None
    subscribed_views: Set[str] = field(default_factory=set)
    execution_history: List[str] = field(default_factory=list)  # execution IDs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "status": self.status,
            "registered_at": self.registered_at.isoformat(),
            "total_executions": self.total_executions,
            "total_tokens_consumed": self.total_tokens_consumed,
            "total_tokens_saved": self.total_tokens_saved,
            "last_execution_at": self.last_execution_at.isoformat() if self.last_execution_at else None,
            "subscribed_views": sorted(self.subscribed_views),
            "recent_executions": self.execution_history[-10:],
        }


@dataclass
class CoordinationEvent:
    """Record of a coordination action between agents."""

    event_id: str
    event_type: str  # execution, delegation, view_access, state_sync
    source_agent_id: str
    target_agent_id: Optional[str] = None
    workspace_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source_agent_id": self.source_agent_id,
            "target_agent_id": self.target_agent_id,
            "workspace_id": self.workspace_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class AgentStateRegistry:
    """Deterministic, replay-compatible agent state tracking.

    Manages agent registrations, coordination events, and provides
    consistent views into agent runtime state.
    """

    def __init__(self, max_event_history: int = 10000):
        self.max_event_history = max_event_history
        self._agents: Dict[str, AgentRegistration] = {}
        self._events: List[CoordinationEvent] = []
        self._execution_index: Dict[str, str] = {}  # execution_id -> agent_id

    def register_agent(
        self,
        agent_type: AgentType,
        agent_id: Optional[str] = None,
    ) -> AgentRegistration:
        """Register a new agent instance."""
        resolved_id = agent_id or f"{agent_type.value}-{uuid.uuid4().hex[:8]}"
        capabilities = AGENT_CAPABILITIES.get(agent_type, AgentCapabilities(
            primary_objective="general",
            semantic_strengths=[],
            output_type="generic",
        ))

        registration = AgentRegistration(
            agent_id=resolved_id,
            agent_type=agent_type,
            capabilities=capabilities,
        )
        self._agents[resolved_id] = registration

        from app.agent_runtime.agents import AGENT_VIEW_MAP
        view = AGENT_VIEW_MAP.get(agent_type)
        if view:
            registration.subscribed_views.add(view)

        self._record_event(CoordinationEvent(
            event_id=f"reg-{resolved_id}",
            event_type="registration",
            source_agent_id=resolved_id,
            metadata={"agent_type": agent_type.value},
        ))

        return registration

    def get_agent(self, agent_id: str) -> Optional[AgentRegistration]:
        return self._agents.get(agent_id)

    def get_agents_by_type(self, agent_type: AgentType) -> List[AgentRegistration]:
        return [a for a in self._agents.values() if a.agent_type == agent_type]

    def get_active_agents(self) -> List[AgentRegistration]:
        return [a for a in self._agents.values() if a.status != "completed"]

    def update_agent_status(self, agent_id: str, status: str) -> None:
        agent = self._agents.get(agent_id)
        if agent:
            agent.status = status

    def record_execution(
        self,
        agent_id: str,
        execution_id: str,
        tokens_consumed: int = 0,
        tokens_saved: int = 0,
    ) -> None:
        """Record that an agent completed an execution."""
        agent = self._agents.get(agent_id)
        if not agent:
            return
        agent.total_executions += 1
        agent.total_tokens_consumed += tokens_consumed
        agent.total_tokens_saved += tokens_saved
        agent.last_execution_at = datetime.now(timezone.utc)
        agent.execution_history.append(execution_id)
        self._execution_index[execution_id] = agent_id

        self._record_event(CoordinationEvent(
            event_id=f"exec-{execution_id}",
            event_type="execution",
            source_agent_id=agent_id,
            metadata={
                "execution_id": execution_id,
                "tokens_consumed": tokens_consumed,
                "tokens_saved": tokens_saved,
            },
        ))

    def record_delegation(
        self,
        source_agent_id: str,
        target_agent_id: str,
        delegation_id: str,
        workspace_id: str = "",
    ) -> None:
        """Record a delegation event between agents."""
        self._record_event(CoordinationEvent(
            event_id=f"deleg-{delegation_id}",
            event_type="delegation",
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            workspace_id=workspace_id,
            metadata={"delegation_id": delegation_id},
        ))

    def get_coordination_timeline(
        self,
        workspace_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[CoordinationEvent]:
        """Get coordination events, optionally filtered by workspace."""
        events = self._events
        if workspace_id:
            events = [e for e in events if e.workspace_id == workspace_id]
        return events[-limit:]

    def get_registry_summary(self) -> Dict[str, Any]:
        """Get summary of agent registry state."""
        agents = list(self._agents.values())
        by_type: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for a in agents:
            by_type[a.agent_type.value] = by_type.get(a.agent_type.value, 0) + 1
            by_status[a.status] = by_status.get(a.status, 0) + 1

        return {
            "total_agents": len(agents),
            "by_type": by_type,
            "by_status": by_status,
            "total_events": len(self._events),
            "total_executions": sum(a.total_executions for a in agents),
            "total_tokens_consumed": sum(a.total_tokens_consumed for a in agents),
            "total_tokens_saved": sum(a.total_tokens_saved for a in agents),
        }

    def export_registry(self, output_file: str) -> str:
        """Export registry state to JSON."""
        payload = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "summary": self.get_registry_summary(),
            "agents": {aid: a.to_dict() for aid, a in self._agents.items()},
            "recent_events": [e.to_dict() for e in self._events[-200:]],
        }
        with open(output_file, "w") as f:
            json.dump(payload, f, indent=2)
        return output_file

    def _record_event(self, event: CoordinationEvent) -> None:
        self._events.append(event)
        if len(self._events) > self.max_event_history:
            self._events = self._events[-self.max_event_history:]
