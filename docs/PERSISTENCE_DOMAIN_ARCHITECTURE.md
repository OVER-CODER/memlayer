# Persistence Domain Architecture — MemLayer Production Storage

## 1. Architectural Strategy
MemLayer production storage is divided into distinct **Persistence Domains** based on data mutability, volume, access patterns, and trust requirements. This separation ensures that high-volume immutable data (traces) does not interfere with critical mutable metadata (workspaces).

## 2. Domain Definitions

| Domain | Characteristic | Storage Pattern | Primary Strategy |
| :--- | :--- | :--- | :--- |
| **Workspace State** | Mutable Relational | SQL Table | ACID transactions for metadata. |
| **Semantic Memories** | Relational + Vector | SQL + pgvector | High-frequency append; Indexed vector search. |
| **Compiled Projections** | Immutable-ish | SQL + JSONB | Deterministic cache of role-specific contexts. |
| **Replay Traces** | Immutable Append | JSONB / Blob | Replay-centric traversal; High-density storage. |
| **Governance Audit** | Immutable Append | SQL (Append-Only) | Integrity-hashed records; Audit-locked rows. |
| **Semantic Lineage** | Graph-like Ancestry | SQL (Recursive) | Parent-Child pointers; Ancestry path indexing. |
| **Telemetry** | Time-Series | Hypertable (Optional) | High-volume events; Partitioned by timestamp. |
| **Coordination Events**| Event Log | SQL (Append-Only) | Inter-agent delegation traces. |
| **Snapshots** | Blob / Archive | Object Storage | Compressed binary/JSON blocks for recovery. |

## 3. Mutability Rules

### Domain A: Mutable Metadata (Workspaces, Sessions)
- **Rules**: Supports `UPDATE` and `DELETE`. 
- **Consistency**: Immediate consistency required.
- **Example**: Changing a workspace name or updating a user's session token.

### Domain B: Immutable Cognition (Memories, Projections)
- **Rules**: `INSERT` only. `DELETE` allowed only for tenant purging. No `UPDATE`.
- **Consistency**: Deterministic ordering via sequence numbers.
- **Example**: Ingesting a new utterance or compiling a Research View.

### Domain C: Immutable Trust (Audit, Lineage, Traces)
- **Rules**: Strictly `INSERT` only. Rows are integrity-hashed.
- **Consistency**: Replay-linked. Traces must be commit-atomic with the execution result.
- **Example**: Recording a coordination result or a semantic checkpoint.

## 4. Indexing Strategy

### Replay Indexing
- Primary Index: `(workspace_id, trace_id)`
- Secondary Index: `(provider, query_type, timestamp)`
- **Goal**: Sub-millisecond lookup of historical traces for deterministic replay.

### Lineage Indexing
- Recursive Index: `(child_id, parent_id)`
- Ancestry Index: `(workspace_id, checkpoint_depth)`
- **Goal**: Rapid reconstruction of reasoning chains for the Governance Explorer.

### Telemetry Indexing
- Partition Key: `timestamp`
- Grouping Key: `(trace_id, stage)`
- **Goal**: High-speed aggregation of token metrics and latency profiles.

## 5. Tenant Isolation Constraints
Every table across ALL domains MUST include a `tenant_id` column. 
- **Row-Level Security (RLS)**: Enforced at the PostgreSQL layer to prevent cross-tenant data leakage.
- **Index Isolation**: All indexes are prefixed with `tenant_id` to ensure optimal query isolation.

## 6. Archival Implications
- **Hot Storage (PostgreSQL)**: Last 30 days of traces and telemetry.
- **Warm Storage (Object Storage)**: Snapshots and older replay traces.
- **Cold Storage (Archive)**: Historical audit trails for compliance.
