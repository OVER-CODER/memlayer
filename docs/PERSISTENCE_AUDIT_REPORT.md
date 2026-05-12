# Persistence Audit Report — MemLayer Cognition Infrastructure

## 1. Executive Summary
The current persistence architecture of MemLayer is a hybrid of synchronous relational storage (SQLite) and volatile in-memory registries. While the system effectively maintains determinism for individual executions, it lacks the durable, scalable, and isolated substrate required for production-grade cognition infrastructure.

## 2. Current Storage Flows

| Subsystem | Storage Mechanism | Mutability | Persistence Mode |
| :--- | :--- | :--- | :--- |
| **Workspace Metadata** | SQLite (`workspaces`) | Mutable | Synchronous DB |
| **Semantic Memories** | SQLite (`memories`) | Immutable | Synchronous DB |
| **Replay Traces** | In-Memory (`Dict`) | Immutable | Volatile (Manual JSON Export) |
| **Governance Audit** | In-Memory (`List`) | Append-Only | Volatile (Manual JSON Export) |
| **Semantic Lineage** | In-Memory (`Dict`) | Immutable | Volatile (Manual JSON Export) |
| **Telemetry Events** | In-Memory (`List`) | Append-Only | Volatile (Manual JSON Export) |
| **Workspace States** | Filesystem (`JSON`) | Mutable | Synchronous File I/O |

## 3. Production Blockers & Scalability Bottlenecks

### 1. Volatile Trust Layer (Critical)
The most critical blocker is that **Governance (Audit/Lineage)** and **Replay** data exist primarily in-memory. A system restart results in the loss of all historical traces and audit trails unless a manual export was performed. This violates the core principle of a "Durable Cognition Substrate."

### 2. Synchronous DB Contention
The reliance on synchronous SQLAlchemy calls with SQLite will lead to write-ahead log (WAL) contention in multi-tenant environments. Every memory ingestion or coordination event blocks the execution loop for I/O.

### 3. Singleton Runtime Coupling
The current architecture assumes a singleton instance where all runtime services (Replay, Telemetry, etc.) are local objects. This prevents horizontal scaling and high-availability (HA) deployment.

### 4. Fragmented Persistence Logic
Persistence is scattered across:
- `app/db/models.py` (User data)
- `app/deployment/workspace_persistence.py` (Workspace state)
- Individual service `__init__` methods (In-memory registries)

## 4. Deterministic Assumptions
The system currently relies on:
- `json.dumps(sort_keys=True)` for stable hashing.
- ISO 8601 UTC strings for timestamp stabilization.
- Python `uuid` for identifier generation.
- Python `hashlib` for integrity checks.

These are technically sound but are not enforced by the storage layer (e.g., SQLite doesn't enforce JSON ordering or timestamp canonicalization).

## 5. Scalability Limits
- **Memory Growth**: In-memory telemetry and replay history will eventually cause Out-of-Memory (OOM) failures under heavy longitudinal workloads (e.g., LoCoMo dataset).
- **Vector Search**: Current "Vector" type in SQLite is a custom decorator that serializes to JSON strings, making vector similarity searches slow and non-indexed.

## 6. Audit Conclusion
MemLayer requires a total transition from **"In-Memory Registries"** to **"Abstracted Repository Layers"** backed by a production-grade database (PostgreSQL + pgvector). The Trust Layer must be made durable without sacrificing the sub-millisecond determinism of the runtime.
