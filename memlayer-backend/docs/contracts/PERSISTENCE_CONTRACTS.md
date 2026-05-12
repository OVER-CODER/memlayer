# Persistence Layer Contracts — v1

## 1. Overview
Defines the storage and retrieval guarantees for the MemLayer persistent substrate.

## 2. Unit of Work (UoW)
- **Contract**: `SQLUnitOfWork` ensures that `Lineage`, `Memories`, and `Traces` are committed atomically.
- **Guarantee**: "All or Nothing." No partial state updates for a cognitive turn.

## 3. Repository Isolation
- **Rule**: All queries MUST inject `tenant_id` from the context.
- **Forbidden**: Cross-tenant data access (except via `PlatformAdmin` internal tools).

## 4. Lineage Integrity
- **Immutability**: `semantic_lineage` records are append-only.
- **Ancestry**: `parent_id` MUST exist before a child record is committed.
- **Hash Chain**: Every record contains an `integrity_hash` of its content and its parent's hash.

## 5. Memory Retrieval
- **Metric**: Cosine Similarity.
- **Index**: pgvector HNSW (Production) or SQLite Scan (Dev).
- **Guarantee**: Stability. The same query against the same memory set MUST return identical ranking order.

## 6. Snapshot Durability
- **Storage**: `IObjectStorageProvider`.
- **Contract**: Snapshots must be verifiable via SHA256 manifest.
- **Rule**: Objects are stored at `{tenant_id}/{workspace_id}/snapshots/{id}.tar.gz`.

## 7. Migration Constraint
- Schema changes MUST NOT invalidate historical `ReplayTrace` serialization.
- Columns used for `CanonicalSerializer` (content, metadata) MUST NOT be renamed or deleted.
