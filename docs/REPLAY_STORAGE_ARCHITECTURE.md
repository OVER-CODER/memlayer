# Replay Storage Architecture — Deterministic Reproducibility

## 1. Overview
Replay Storage is the high-fidelity durable layer for MemLayer. It ensures that every execution, coordination, and derivation can be perfectly reconstructed. It moves MemLayer from "Transient AI" to "Reproducible Cognition Infrastructure."

## 2. Storage Strategy

### 2.1. Trace Decomposition
To optimize storage and retrieval, replay traces are decomposed into:
- **Trace Header**: Meta-parameters (Query, Provider, Budget). Stored in `replay_traces`.
- **Execution Plan**: The deterministic DAG of compilation. Stored in `replay_traces.execution_plan` (JSONB).
- **Stage Records**: Granular telemetry for every stage. Stored in `telemetry_events` and linked via `trace_id`.
- **Semantic Checkpoints**: The state of the workspace before/after. Stored in `semantic_lineage` and linked via `integrity_hash`.

### 2.2. Delta vs. Full Checkpoints
- **Baseline Snapshots**: Periodically, a full workspace state is snapshotted.
- **Delta Traces**: In-between snapshots, only the *changes* (new memories, modified weights) and the *derivation logic* are stored.
- **Reconstruction**: To replay Turn N, the system loads Baseline Snapshot S and applies Delta Traces S+1 to N.

## 3. Determinism Guarantees

### 3.1. Canonical Serialization
Every trace object is passed through the `CanonicalSerializer` before being hashed or stored. This ensures that:
- Dictionary key ordering is stable.
- Floating point precision is preserved/standardized.
- Timestamps are UTC ISO 8601.

### 3.2. Integrity Hashing
`trace_checksum = SHA256(CanonicalJSON(Header + ExecutionPlan + MemoryIDs))`
Before a replay starts, the engine re-calculates the checksum. If it doesn't match the stored `integrity_hash`, the replay is aborted to prevent non-deterministic outcomes.

## 4. Traversal Optimization
Replay traces are indexed by `(workspace_id, timestamp DESC)`. 
- **Time-Travel**: Operators can "jump" to any point in the cognition history by selecting a `trace_id`.
- **Branching**: A replay can be "forked" from a historical trace into a new workspace for hypothesis testing without modifying the original lineage.

## 5. Storage Efficiency
- **JSONB Compression**: PostgreSQL JSONB provides transparent compression for repeated keys.
- **Deduplication**: If multiple traces share the same `ExecutionPlan` (e.g., repeating a query), only one plan is stored, and traces reference its hash.
- **Pruning Policies**: 
  - `Detailed Traces`: Kept for 30 days.
  - `Summary Traces`: Kept for 1 year.
  - `Governance Audit`: Kept forever.

## 6. Implementation Checklist
- [x] Define `ReplayableTrace` SQLAlchemy Model.
- [ ] Implement `ReplayTraceRepository` with async support.
- [ ] Integrate `CanonicalSerializer` into the Replay Engine flow.
- [ ] Implement `TraceIntegrityMonitor` to validate checksums on load.
