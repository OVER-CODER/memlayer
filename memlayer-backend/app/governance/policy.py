"""
Governance Policy Engine for MemLayer.

Enforces runtime governance policies that remain deterministic and replayable.
Policies focus on runtime trust, not enterprise RBAC/auth systems.
All policy operations are tenant-scoped and isolated.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class PolicyDecisionType(str, Enum):
    """Policy decision outcomes."""

    APPROVED = "approved"
    DENIED = "denied"
    WARNING = "warning"


@dataclass(frozen=True)
class PolicyDefinition:
    """Immutable policy definition."""

    policy_id: str
    policy_name: str
    description: str
    tenant_id: str
    rules: Dict[str, Any]  # Policy-specific rule configuration
    priority: int  # Higher = evaluated first
    enabled: bool = True


@dataclass(frozen=True)
class PolicyDecision:
    """Immutable policy decision record."""

    decision_id: str
    policy_id: str
    workspace_id: str
    tenant_id: str
    decision: str  # PolicyDecisionType value
    confidence: float  # 0-1.0
    reasons: List[str]
    enforcement_action: Optional[str]
    timestamp: str  # ISO 8601 UTC
    context_summary: Dict[str, Any]


@dataclass(frozen=True)
class PolicyViolation:
    """Record of a policy violation."""

    violation_id: str
    policy_id: str
    workspace_id: str
    tenant_id: str
    violation_type: str
    severity: str  # "low", "medium", "high", "critical"
    details: Dict[str, Any]
    timestamp: str  # ISO 8601 UTC
    remediation_actions: List[str]


class GovernancePolicyEngine:
    """
    Manages runtime governance policies.

    All policy operations are:
    - Deterministic (same inputs -> same decisions)
    - Replayable (decisions can be reconstructed from audit trail)
    - Tenant-isolated (scoped by tenant_id)
    - Runtime-focused (not enterprise RBAC/auth)
    """

    def __init__(self):
        """Initialize policy engine."""
        # policies[tenant_id] = dict of policy_id -> PolicyDefinition
        self._policies: Dict[str, Dict[str, PolicyDefinition]] = {}

        # Policy decisions history
        self._decisions: Dict[str, List[PolicyDecision]] = {}

        # Policy violations
        self._violations: Dict[str, List[PolicyViolation]] = {}

        # Sequence counters for IDs
        self._decision_counter: Dict[str, int] = {}
        self._violation_counter: Dict[str, int] = {}

        # Built-in policy evaluators (deterministic functions)
        self._policy_evaluators: Dict[str, Callable] = {
            "replay_integrity": self._evaluate_replay_integrity_policy,
            "semantic_continuity": self._evaluate_semantic_continuity_policy,
            "tenant_boundary": self._evaluate_tenant_boundary_policy,
            "resource_governance": self._evaluate_resource_governance_policy,
            "coordination_stability": self._evaluate_coordination_stability_policy,
        }

    def register_policy(
        self,
        policy_id: str,
        policy_name: str,
        description: str,
        policy_type: str,
        rules: Dict[str, Any],
        tenant_id: str,
        priority: int = 100,
    ) -> bool:
        """
        Register a governance policy.

        Args:
            policy_id: Unique policy identifier
            policy_name: Human-readable policy name
            description: Policy description
            policy_type: Type of policy (determines evaluator)
            rules: Policy-specific configuration
            tenant_id: Tenant identifier
            priority: Evaluation priority (higher first)

        Returns:
            True if registered successfully
        """
        if tenant_id not in self._policies:
            self._policies[tenant_id] = {}

        # Check if policy already exists
        if policy_id in self._policies[tenant_id]:
            return False

        policy = PolicyDefinition(
            policy_id=policy_id,
            policy_name=policy_name,
            description=description,
            tenant_id=tenant_id,
            rules={"type": policy_type, **rules},
            priority=priority,
            enabled=True,
        )

        self._policies[tenant_id][policy_id] = policy
        return True

    def evaluate_policy(
        self,
        workspace_id: str,
        policy_id: str,
        context: Dict[str, Any],
        tenant_id: str,
    ) -> PolicyDecision:
        """
        Evaluate a policy in given context.

        Args:
            workspace_id: Workspace identifier
            policy_id: Policy identifier
            context: Context for evaluation
            tenant_id: Tenant identifier (for isolation)

        Returns:
            PolicyDecision with evaluation result
        """
        # Verify policy exists and belongs to tenant
        if tenant_id not in self._policies:
            return self._create_denied_decision(
                workspace_id,
                policy_id,
                tenant_id,
                ["Policy not found for tenant"],
                context,
            )

        if policy_id not in self._policies[tenant_id]:
            return self._create_denied_decision(
                workspace_id,
                policy_id,
                tenant_id,
                ["Policy not registered for this tenant"],
                context,
            )

        policy = self._policies[tenant_id][policy_id]

        if not policy.enabled:
            return self._create_denied_decision(
                workspace_id, policy_id, tenant_id, ["Policy is disabled"], context
            )

        # Get policy type
        policy_type = policy.rules.get("type", "unknown")

        # Evaluate using appropriate evaluator
        if policy_type in self._policy_evaluators:
            evaluator = self._policy_evaluators[policy_type]
            return evaluator(workspace_id, policy_id, policy, context, tenant_id)

        # Unknown policy type
        return self._create_denied_decision(
            workspace_id,
            policy_id,
            tenant_id,
            [f"Unknown policy type: {policy_type}"],
            context,
        )

    def enforce_policy(
        self,
        workspace_id: str,
        policy_id: str,
        context: Dict[str, Any],
        tenant_id: str,
    ) -> Dict[str, Any]:
        """
        Enforce a policy (evaluate + record decision).

        Args:
            workspace_id: Workspace identifier
            policy_id: Policy identifier
            context: Context for evaluation
            tenant_id: Tenant identifier

        Returns:
            Dictionary with enforcement result
        """
        decision = self.evaluate_policy(workspace_id, policy_id, context, tenant_id)

        # Record decision
        if workspace_id not in self._decisions:
            self._decisions[workspace_id] = []

        self._decisions[workspace_id].append(decision)

        # Record violation if denied
        if decision.decision == PolicyDecisionType.DENIED:
            violation = self._create_violation_from_decision(decision, workspace_id)
            if workspace_id not in self._violations:
                self._violations[workspace_id] = []
            self._violations[workspace_id].append(violation)

        return {
            "enforced": True,
            "decision": decision.decision,
            "confidence": decision.confidence,
            "reasons": decision.reasons,
            "action": decision.enforcement_action,
        }

    def get_policy_violations(
        self, workspace_id: str, tenant_id: str
    ) -> List[PolicyViolation]:
        """
        Get policy violations for workspace (tenant-scoped).

        Args:
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier

        Returns:
            List of violations
        """
        if workspace_id not in self._violations:
            return []

        violations = self._violations[workspace_id]
        return [v for v in violations if v.tenant_id == tenant_id]

    def get_policy_decisions(
        self, workspace_id: str, tenant_id: str, policy_id: Optional[str] = None
    ) -> List[PolicyDecision]:
        """
        Get policy decisions for workspace (tenant-scoped).

        Args:
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier
            policy_id: Optional filter by specific policy

        Returns:
            List of decisions
        """
        if workspace_id not in self._decisions:
            return []

        decisions = self._decisions[workspace_id]
        decisions = [d for d in decisions if d.tenant_id == tenant_id]

        if policy_id:
            decisions = [d for d in decisions if d.policy_id == policy_id]

        return decisions

    def get_policy_statistics(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get statistics for policies (tenant-scoped).

        Args:
            tenant_id: Tenant identifier

        Returns:
            Statistics dictionary
        """
        if tenant_id not in self._policies:
            return {
                "tenant_id": tenant_id,
                "total_policies": 0,
                "enabled_policies": 0,
            }

        policies = self._policies[tenant_id]

        return {
            "tenant_id": tenant_id,
            "total_policies": len(policies),
            "enabled_policies": sum(1 for p in policies.values() if p.enabled),
            "policies": [
                {"policy_id": p.policy_id, "name": p.policy_name}
                for p in policies.values()
            ],
        }

    # Policy Evaluators (Deterministic)

    def _evaluate_replay_integrity_policy(
        self,
        workspace_id: str,
        policy_id: str,
        policy: PolicyDefinition,
        context: Dict[str, Any],
        tenant_id: str,
    ) -> PolicyDecision:
        """Evaluate replay integrity policy."""
        reasons: List[str] = []

        # Check replay divergence threshold
        divergence = context.get("replay_divergence_count", 0)
        max_divergence = policy.rules.get("max_divergence_count", 0)

        if divergence > max_divergence:
            reasons.append(
                f"Replay divergence {divergence} exceeds threshold {max_divergence}"
            )

        # Check semantic match ratio
        semantic_matches = context.get("semantic_matches", 0)
        total_expectations = context.get("total_expectations", 1)
        min_match_ratio = policy.rules.get("min_semantic_match_ratio", 0.99)

        if total_expectations > 0:
            match_ratio = semantic_matches / total_expectations
            if match_ratio < min_match_ratio:
                reasons.append(
                    f"Semantic match ratio {match_ratio:.2%} "
                    f"below threshold {min_match_ratio:.2%}"
                )

        if reasons:
            return self._create_denied_decision(
                workspace_id, policy_id, tenant_id, reasons, context
            )

        return self._create_approved_decision(
            workspace_id, policy_id, tenant_id, ["Replay integrity verified"], context
        )

    def _evaluate_semantic_continuity_policy(
        self,
        workspace_id: str,
        policy_id: str,
        policy: PolicyDefinition,
        context: Dict[str, Any],
        tenant_id: str,
    ) -> PolicyDecision:
        """Evaluate semantic continuity policy."""
        reasons: List[str] = []

        # Check semantic state corruption
        corruption_detected = context.get("semantic_corruption", False)
        if corruption_detected:
            reasons.append("Semantic state corruption detected")

        # Check for semantic drift
        semantic_drift = context.get("semantic_drift", 0.0)
        max_drift = policy.rules.get("max_semantic_drift", 0.05)

        if semantic_drift > max_drift:
            reasons.append(
                f"Semantic drift {semantic_drift:.2%} exceeds threshold {max_drift:.2%}"
            )

        if reasons:
            return self._create_denied_decision(
                workspace_id, policy_id, tenant_id, reasons, context
            )

        return self._create_approved_decision(
            workspace_id,
            policy_id,
            tenant_id,
            ["Semantic continuity maintained"],
            context,
        )

    def _evaluate_tenant_boundary_policy(
        self,
        workspace_id: str,
        policy_id: str,
        policy: PolicyDefinition,
        context: Dict[str, Any],
        tenant_id: str,
    ) -> PolicyDecision:
        """Evaluate tenant boundary isolation policy."""
        reasons: List[str] = []

        # Check for cross-tenant access
        context_tenant = context.get("context_tenant_id", tenant_id)
        if context_tenant != tenant_id:
            reasons.append(
                f"Cross-tenant access attempted: {context_tenant} != {tenant_id}"
            )

        # Check for cross-tenant data references
        referenced_tenants = context.get("referenced_tenants", [])
        if tenant_id not in referenced_tenants and len(referenced_tenants) > 0:
            reasons.append(f"Data references external tenants: {referenced_tenants}")

        if reasons:
            return self._create_denied_decision(
                workspace_id, policy_id, tenant_id, reasons, context
            )

        return self._create_approved_decision(
            workspace_id,
            policy_id,
            tenant_id,
            ["Tenant boundary isolation maintained"],
            context,
        )

    def _evaluate_resource_governance_policy(
        self,
        workspace_id: str,
        policy_id: str,
        policy: PolicyDefinition,
        context: Dict[str, Any],
        tenant_id: str,
    ) -> PolicyDecision:
        """Evaluate resource governance policy."""
        reasons: List[str] = []

        # Check memory usage
        memory_used = context.get("memory_used_mb", 0)
        max_memory = policy.rules.get("max_memory_mb", 1024)

        if memory_used > max_memory:
            reasons.append(f"Memory usage {memory_used}MB exceeds limit {max_memory}MB")

        # Check tensor count
        tensor_count = context.get("tensor_count", 0)
        max_tensors = policy.rules.get("max_tensors", 10000)

        if tensor_count > max_tensors:
            reasons.append(f"Tensor count {tensor_count} exceeds limit {max_tensors}")

        if reasons:
            return self._create_denied_decision(
                workspace_id, policy_id, tenant_id, reasons, context
            )

        return self._create_approved_decision(
            workspace_id,
            policy_id,
            tenant_id,
            ["Resource usage within limits"],
            context,
        )

    def _evaluate_coordination_stability_policy(
        self,
        workspace_id: str,
        policy_id: str,
        policy: PolicyDefinition,
        context: Dict[str, Any],
        tenant_id: str,
    ) -> PolicyDecision:
        """Evaluate coordination stability policy."""
        reasons: List[str] = []

        # Check coordination error rate
        coordination_failures = context.get("coordination_failures", 0)
        coordination_attempts = context.get("coordination_attempts", 1)
        max_error_rate = policy.rules.get("max_error_rate", 0.01)

        if coordination_attempts > 0:
            error_rate = coordination_failures / coordination_attempts
            if error_rate > max_error_rate:
                reasons.append(
                    f"Coordination error rate {error_rate:.2%} "
                    f"exceeds threshold {max_error_rate:.2%}"
                )

        # Check for coordination stalls
        stall_detected = context.get("coordination_stall", False)
        if stall_detected:
            reasons.append("Coordination stall detected")

        if reasons:
            return self._create_denied_decision(
                workspace_id, policy_id, tenant_id, reasons, context
            )

        return self._create_approved_decision(
            workspace_id,
            policy_id,
            tenant_id,
            ["Coordination stability maintained"],
            context,
        )

    # Helper methods

    def _create_approved_decision(
        self,
        workspace_id: str,
        policy_id: str,
        tenant_id: str,
        reasons: List[str],
        context: Dict[str, Any],
    ) -> PolicyDecision:
        """Create an approved policy decision."""
        sequence = self._decision_counter.get(workspace_id, 0) + 1
        self._decision_counter[workspace_id] = sequence

        decision_id = f"{workspace_id}:{tenant_id}:dec:{sequence:08d}"
        timestamp = datetime.now(timezone.utc).isoformat()

        return PolicyDecision(
            decision_id=decision_id,
            policy_id=policy_id,
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            decision=PolicyDecisionType.APPROVED,
            confidence=1.0,
            reasons=reasons,
            enforcement_action=None,
            timestamp=timestamp,
            context_summary=self._summarize_context(context),
        )

    def _create_denied_decision(
        self,
        workspace_id: str,
        policy_id: str,
        tenant_id: str,
        reasons: List[str],
        context: Dict[str, Any],
    ) -> PolicyDecision:
        """Create a denied policy decision."""
        sequence = self._decision_counter.get(workspace_id, 0) + 1
        self._decision_counter[workspace_id] = sequence

        decision_id = f"{workspace_id}:{tenant_id}:dec:{sequence:08d}"
        timestamp = datetime.now(timezone.utc).isoformat()

        return PolicyDecision(
            decision_id=decision_id,
            policy_id=policy_id,
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            decision=PolicyDecisionType.DENIED,
            confidence=1.0,
            reasons=reasons,
            enforcement_action="BLOCK",
            timestamp=timestamp,
            context_summary=self._summarize_context(context),
        )

    def _create_violation_from_decision(
        self, decision: PolicyDecision, workspace_id: str
    ) -> PolicyViolation:
        """Create a policy violation record from a denied decision."""
        sequence = self._violation_counter.get(workspace_id, 0) + 1
        self._violation_counter[workspace_id] = sequence

        violation_id = f"{workspace_id}:{sequence:08d}"

        return PolicyViolation(
            violation_id=violation_id,
            policy_id=decision.policy_id,
            workspace_id=workspace_id,
            tenant_id=decision.tenant_id,
            violation_type=decision.policy_id,
            severity="high",
            details={"reasons": decision.reasons},
            timestamp=decision.timestamp,
            remediation_actions=[decision.enforcement_action or "INVESTIGATE"],
        )

    @staticmethod
    def _summarize_context(context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of context for decision record."""
        summary: Dict[str, Any] = {}

        # Include numeric and string values, skip complex objects
        for key, value in context.items():
            if isinstance(value, (int, float, str, bool)):
                summary[key] = value

        return summary
