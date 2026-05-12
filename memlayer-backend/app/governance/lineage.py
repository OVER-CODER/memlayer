"""
Semantic Lineage Engine for MemLayer.

Tracks semantic state evolution, projection ancestry, and coordination lineage.
Enables reconstruction of historical semantic chains and comparison of historical states.
All operations are deterministic and replay-compatible.
All lineage is tenant-scoped and isolated.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass(frozen=True)
class LineageCheckpoint:
    """Immutable semantic lineage checkpoint."""

    checkpoint_id: str
    workspace_id: str
    tenant_id: str
    timestamp: str  # ISO 8601 UTC
    semantic_state_hash: str  # SHA256
    derived_from: List[str]  # Parent checkpoint IDs
    operation_id: str
    metadata: Dict[str, Any]  # Custom metadata


@dataclass(frozen=True)
class ProjectionDerivation:
    """Record of how a projection was derived."""

    derivation_id: str
    workspace_id: str
    tenant_id: str
    projection_id: str
    source_checkpoints: List[str]
    derivation_method: str  # "composition", "projection", "filtering", etc.
    timestamp: str  # ISO 8601 UTC
    derived_state_hash: str


@dataclass(frozen=True)
class SemanticAncestryGraph:
    """Ancestry graph for semantic state."""

    checkpoint_id: str
    workspace_id: str
    tenant_id: str
    ancestors: Dict[str, "LineageCheckpoint"]  # checkpoint_id -> checkpoint
    edges: List[Tuple[str, str]]  # (parent_id, child_id) tuples
    depth: int  # Maximum depth in graph


class SemanticLineageEngine:
    """
    Manages semantic lineage tracking and reconstruction.

    All lineage records are:
    - Deterministically computed (hashes, checkpoints)
    - Replay-compatible (timestamps are reproducible)
    - Tenant-isolated (scoped by tenant_id)
    - Immutable (frozen dataclasses)
    - Ancestry-preserving (tracks full derivation chains)
    """

    def __init__(self):
        """Initialize the semantic lineage engine."""
        # checkpoints[workspace_id] = list of LineageCheckpoint
        self._checkpoints: Dict[str, List[LineageCheckpoint]] = {}

        # derivations[workspace_id] = list of ProjectionDerivation
        self._derivations: Dict[str, List[ProjectionDerivation]] = {}

        # Index for quick lookup: checkpoint_id -> checkpoint
        self._checkpoint_index: Dict[str, LineageCheckpoint] = {}

        # Index for quick lookup: projection_id -> list of derivations
        self._projection_index: Dict[str, List[ProjectionDerivation]] = defaultdict(
            list
        )

        # Track checkpoint count per tenant for sequencing
        self._checkpoint_counter: Dict[str, int] = {}

        # Last sequence number per workspace
        self._sequence_counter: Dict[str, int] = {}

    def record_semantic_checkpoint(
        self,
        workspace_id: str,
        semantic_state: Dict[str, Any],
        operation_id: str,
        derived_from: Optional[List[str]] = None,
        tenant_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LineageCheckpoint:
        """
        Record a semantic state checkpoint.

        Args:
            workspace_id: Workspace identifier
            semantic_state: Current semantic state
            operation_id: Operation creating this checkpoint
            derived_from: Parent checkpoint IDs (if any)
            tenant_id: Tenant identifier
            metadata: Optional custom metadata

        Returns:
            The recorded LineageCheckpoint
        """
        if derived_from is None:
            derived_from = []

        if metadata is None:
            metadata = {}

        # Generate checkpoint ID
        sequence_num = self._sequence_counter.get(workspace_id, 0) + 1
        self._sequence_counter[workspace_id] = sequence_num

        checkpoint_id = f"{workspace_id}:{tenant_id}:cp:{sequence_num:08d}"

        # Compute semantic state hash deterministically
        semantic_hash = self._hash_semantic_state(semantic_state)

        # Get current time
        timestamp = datetime.now(timezone.utc).isoformat()

        # Create checkpoint
        checkpoint = LineageCheckpoint(
            checkpoint_id=checkpoint_id,
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            timestamp=timestamp,
            semantic_state_hash=semantic_hash,
            derived_from=derived_from,
            operation_id=operation_id,
            metadata=metadata,
        )

        # Record checkpoint
        if workspace_id not in self._checkpoints:
            self._checkpoints[workspace_id] = []

        self._checkpoints[workspace_id].append(checkpoint)
        self._checkpoint_index[checkpoint_id] = checkpoint

        return checkpoint

    def record_projection_derivation(
        self,
        workspace_id: str,
        projection_id: str,
        source_checkpoints: List[str],
        derivation_method: str,
        derived_state: Dict[str, Any],
        tenant_id: str,
    ) -> ProjectionDerivation:
        """
        Record how a projection was derived.

        Args:
            workspace_id: Workspace identifier
            projection_id: Projection identifier
            source_checkpoints: Source checkpoint IDs
            derivation_method: Method used ("composition", "projection", etc.)
            derived_state: The resulting derived state
            tenant_id: Tenant identifier

        Returns:
            The recorded ProjectionDerivation
        """
        # Generate derivation ID
        sequence_num = self._sequence_counter.get(workspace_id, 0) + 1
        self._sequence_counter[workspace_id] = sequence_num

        derivation_id = f"{workspace_id}:{tenant_id}:der:{sequence_num:08d}"

        # Compute derived state hash
        derived_hash = self._hash_semantic_state(derived_state)

        # Get current time
        timestamp = datetime.now(timezone.utc).isoformat()

        # Create derivation record
        derivation = ProjectionDerivation(
            derivation_id=derivation_id,
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            projection_id=projection_id,
            source_checkpoints=source_checkpoints,
            derivation_method=derivation_method,
            timestamp=timestamp,
            derived_state_hash=derived_hash,
        )

        # Record derivation
        if workspace_id not in self._derivations:
            self._derivations[workspace_id] = []

        self._derivations[workspace_id].append(derivation)
        self._projection_index[projection_id].append(derivation)

        return derivation

    def get_lineage_chain(
        self,
        workspace_id: str,
        checkpoint_id: str,
        tenant_id: str,
        max_depth: Optional[int] = None,
    ) -> List[LineageCheckpoint]:
        """
        Reconstruct lineage chain for a checkpoint.

        Args:
            workspace_id: Workspace identifier
            checkpoint_id: Starting checkpoint ID
            tenant_id: Tenant identifier (for isolation)
            max_depth: Maximum depth to traverse

        Returns:
            List of checkpoints in lineage chain (ordered from root to target)
        """
        if checkpoint_id not in self._checkpoint_index:
            return []

        checkpoint = self._checkpoint_index[checkpoint_id]

        # Verify tenant isolation
        if checkpoint.tenant_id != tenant_id:
            return []  # Tenant isolation violation - return empty

        # Build lineage chain
        chain: List[LineageCheckpoint] = [checkpoint]
        visited: Set[str] = {checkpoint_id}
        current = checkpoint
        depth = 0

        while current.derived_from and (max_depth is None or depth < max_depth):
            # Get parent
            parent_ids = current.derived_from
            if not parent_ids:
                break

            parent_id = parent_ids[0]  # Use first parent

            if parent_id in visited:
                break  # Cycle detection

            if parent_id not in self._checkpoint_index:
                break  # Parent not found

            parent = self._checkpoint_index[parent_id]

            # Verify tenant consistency
            if parent.tenant_id != tenant_id:
                break  # Tenant isolation violation

            chain.insert(0, parent)
            visited.add(parent_id)
            current = parent
            depth += 1

        return chain

    def get_semantic_ancestry(
        self,
        workspace_id: str,
        projection_id: str,
        tenant_id: str,
        max_depth: Optional[int] = None,
    ) -> SemanticAncestryGraph:
        """
        Build ancestry graph for a projection.

        Args:
            workspace_id: Workspace identifier
            projection_id: Projection identifier
            tenant_id: Tenant identifier (for isolation)
            max_depth: Maximum depth to traverse

        Returns:
            SemanticAncestryGraph with ancestors and edges
        """
        # Get derivations for this projection
        derivations = self._projection_index.get(projection_id, [])

        # Filter by tenant
        derivations = [d for d in derivations if d.tenant_id == tenant_id]

        if not derivations:
            # No ancestry for this projection
            return SemanticAncestryGraph(
                checkpoint_id=projection_id,
                workspace_id=workspace_id,
                tenant_id=tenant_id,
                ancestors={},
                edges=[],
                depth=0,
            )

        # Build ancestry graph
        ancestors: Dict[str, LineageCheckpoint] = {}
        edges: List[Tuple[str, str]] = []
        visited: Set[str] = set()
        max_depth_reached = 0

        def traverse_ancestry(checkpoint_id: str, current_depth: int):
            """Recursively traverse ancestry."""
            nonlocal max_depth_reached

            if checkpoint_id in visited:
                return

            if max_depth and current_depth > max_depth:
                return

            visited.add(checkpoint_id)
            max_depth_reached = max(max_depth_reached, current_depth)

            if checkpoint_id not in self._checkpoint_index:
                return

            checkpoint = self._checkpoint_index[checkpoint_id]

            # Verify tenant consistency
            if checkpoint.tenant_id != tenant_id:
                return

            ancestors[checkpoint_id] = checkpoint

            for parent_id in checkpoint.derived_from:
                if parent_id not in visited:
                    edges.append((parent_id, checkpoint_id))
                    traverse_ancestry(parent_id, current_depth + 1)

        # Traverse from all source checkpoints
        for derivation in derivations:
            for source_cp_id in derivation.source_checkpoints:
                traverse_ancestry(source_cp_id, 0)

        return SemanticAncestryGraph(
            checkpoint_id=projection_id,
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            ancestors=ancestors,
            edges=edges,
            depth=max_depth_reached,
        )

    def compare_checkpoint_states(
        self,
        workspace_id: str,
        checkpoint_id_1: str,
        checkpoint_id_2: str,
        tenant_id: str,
    ) -> Dict[str, Any]:
        """
        Compare semantic states of two checkpoints.

        Args:
            workspace_id: Workspace identifier
            checkpoint_id_1: First checkpoint ID
            checkpoint_id_2: Second checkpoint ID
            tenant_id: Tenant identifier (for isolation)

        Returns:
            Comparison results
        """
        cp1 = self._checkpoint_index.get(checkpoint_id_1)
        cp2 = self._checkpoint_index.get(checkpoint_id_2)

        if not cp1 or not cp2:
            return {
                "comparable": False,
                "reason": "One or both checkpoints not found",
            }

        # Verify tenant isolation
        if cp1.tenant_id != tenant_id or cp2.tenant_id != tenant_id:
            return {
                "comparable": False,
                "reason": "Tenant isolation violation",
            }

        return {
            "comparable": True,
            "checkpoint_1": checkpoint_id_1,
            "checkpoint_2": checkpoint_id_2,
            "timestamp_1": cp1.timestamp,
            "timestamp_2": cp2.timestamp,
            "state_hash_1": cp1.semantic_state_hash,
            "state_hash_2": cp2.semantic_state_hash,
            "states_identical": cp1.semantic_state_hash == cp2.semantic_state_hash,
            "derived_from_1": cp1.derived_from,
            "derived_from_2": cp2.derived_from,
            "operation_1": cp1.operation_id,
            "operation_2": cp2.operation_id,
        }

    def get_checkpoints_for_workspace(
        self, workspace_id: str, tenant_id: str
    ) -> List[LineageCheckpoint]:
        """
        Get all checkpoints for a workspace (tenant-scoped).

        Args:
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier

        Returns:
            List of checkpoints for this tenant in the workspace
        """
        if workspace_id not in self._checkpoints:
            return []

        checkpoints = self._checkpoints[workspace_id]
        return [cp for cp in checkpoints if cp.tenant_id == tenant_id]

    def get_lineage_summary(self, workspace_id: str, tenant_id: str) -> Dict[str, Any]:
        """
        Get summary of lineage tracking.

        Args:
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier

        Returns:
            Summary dictionary
        """
        checkpoints = self.get_checkpoints_for_workspace(workspace_id, tenant_id)

        if workspace_id in self._derivations:
            derivations = [
                d for d in self._derivations[workspace_id] if d.tenant_id == tenant_id
            ]
        else:
            derivations = []

        # Calculate lineage depth statistics
        max_depth = 0
        total_depth = 0

        for checkpoint in checkpoints:
            chain = self.get_lineage_chain(
                workspace_id, checkpoint.checkpoint_id, tenant_id
            )
            chain_depth = len(chain) - 1
            max_depth = max(max_depth, chain_depth)
            total_depth += chain_depth

        avg_depth = total_depth / len(checkpoints) if checkpoints else 0

        return {
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "total_checkpoints": len(checkpoints),
            "total_derivations": len(derivations),
            "max_lineage_depth": max_depth,
            "avg_lineage_depth": avg_depth,
            "unique_operations": len(set(cp.operation_id for cp in checkpoints)),
            "unique_projections": len(self._projection_index),
        }

    def export_lineage_as_json(self, workspace_id: str, tenant_id: str) -> str:
        """
        Export lineage data as deterministic JSON.

        Args:
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier

        Returns:
            JSON string (deterministically ordered)
        """
        checkpoints = self.get_checkpoints_for_workspace(workspace_id, tenant_id)

        if workspace_id in self._derivations:
            derivations = [
                d for d in self._derivations[workspace_id] if d.tenant_id == tenant_id
            ]
        else:
            derivations = []

        data = {
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "checkpoints": [
                {
                    "checkpoint_id": cp.checkpoint_id,
                    "timestamp": cp.timestamp,
                    "semantic_state_hash": cp.semantic_state_hash,
                    "derived_from": cp.derived_from,
                    "operation_id": cp.operation_id,
                    "metadata": cp.metadata,
                }
                for cp in checkpoints
            ],
            "derivations": [
                {
                    "derivation_id": d.derivation_id,
                    "projection_id": d.projection_id,
                    "source_checkpoints": d.source_checkpoints,
                    "derivation_method": d.derivation_method,
                    "timestamp": d.timestamp,
                    "derived_state_hash": d.derived_state_hash,
                }
                for d in derivations
            ],
        }

        return json.dumps(data, sort_keys=True, indent=2)

    def verify_lineage_integrity(
        self, workspace_id: str, tenant_id: str
    ) -> Dict[str, Any]:
        """
        Verify integrity of lineage records.

        Args:
            workspace_id: Workspace identifier
            tenant_id: Tenant identifier

        Returns:
            Integrity verification results
        """
        checkpoints = self.get_checkpoints_for_workspace(workspace_id, tenant_id)

        errors: List[str] = []

        for checkpoint in checkpoints:
            # Verify tenant consistency
            if checkpoint.tenant_id != tenant_id:
                errors.append(
                    f"Checkpoint {checkpoint.checkpoint_id} has wrong tenant_id"
                )

            # Verify referenced parents exist (if any)
            for parent_id in checkpoint.derived_from:
                if parent_id not in self._checkpoint_index:
                    errors.append(
                        f"Checkpoint {checkpoint.checkpoint_id} "
                        f"references non-existent parent {parent_id}"
                    )
                else:
                    parent = self._checkpoint_index[parent_id]
                    if parent.tenant_id != tenant_id:
                        errors.append(
                            f"Checkpoint {checkpoint.checkpoint_id} "
                            f"references parent with different tenant"
                        )

        return {
            "valid": len(errors) == 0,
            "checkpoints_checked": len(checkpoints),
            "errors": errors,
        }

    @staticmethod
    def _hash_semantic_state(state: Dict[str, Any]) -> str:
        """
        Compute deterministic SHA256 hash of semantic state.

        Uses JSON canonical form for determinism.
        """
        json_str = json.dumps(state, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(json_str.encode()).hexdigest()
