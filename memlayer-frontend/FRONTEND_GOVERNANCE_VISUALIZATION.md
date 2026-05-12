# Governance & Lineage Visualization

The Governance subsystem provides an unforgeable view of system execution and semantic ancestry.

## Audit Trails & Policies
- Realtime streams of `action_type` events (e.g., `WORKSPACE_CREATED`, `POLICY_ENFORCEMENT`).
- Rendered in a high-density, terminal-like feed with exact millisecond timestamps and ISO metadata payload dumps.

## Semantic Ancestry Graph
Visualized via `React Flow`.
- Maps `LineageCheckpoint` nodes to their `derived_from` ancestors.
- Allows tracing back exactly how a semantic state was composed and under what provider shaping conditions.
- Layout tracks `checkpoint_id`, `semantic_state_hash`, and deterministic timestamps.
