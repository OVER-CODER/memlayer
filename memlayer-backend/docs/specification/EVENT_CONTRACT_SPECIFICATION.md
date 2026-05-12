# Event Contract Specification — v1

## 1. Overview
Defines the canonical schemas for all runtime events to ensure cross-system compatibility and replay safety.

## 2. Replay Trace Schema
- **Target**: `replay_traces` table.
- **Fields**:
  - `trace_id`: UUID string.
  - `workspace_id`: Foreign key.
  - `tenant_id`: Mandatory scoping.
  - `query`: Raw input string.
  - `execution_plan`: JSON (Deterministic structure).
  - `integrity_hash`: SHA256 of minified plan.
- **Serialization Order**: `trace_id` -> `workspace_id` -> `query` -> `plan`.

## 3. Governance Audit Schema
- **Target**: `governance_audit` table.
- **Fields**:
  - `event_type`: Categorical string (e.g., `AUTH_GRANTED`, `LINEAGE_COMMIT`).
  - `event_data`: JSON context.
  - `recorded_by`: Auth `subject_id`.
  - `integrity_hash`: Chain link hash.

## 4. Telemetry Event Schema
- **Target**: `telemetry_events` table / Prometheus.
- **Labels**: `workspace_id`, `tenant_id`, `provider`, `stage`.
- **Metrics**: See `TELEMETRY_CONTRACTS.md`.

## 5. Lineage Checkpoint Schema
- **Target**: `semantic_lineage` table.
- **Fields**:
  - `checkpoint_id`: UUID.
  - `state_hash`: Merkle root of current memory set.
  - `parent_id`: Nullable (Root only).
  - `operation_id`: Link to generating Trace.

## 6. Immutable Fields
The following fields MUST NEVER be updated once committed:
- `id`, `uuid`, `trace_id`, `checkpoint_id`.
- `tenant_id`.
- `integrity_hash`.
- `timestamp` (recorded at ingestion).

## 7. Serialization Guarantee
All JSON fields in events MUST be serialized using `json.dumps(data, sort_keys=True, separators=(',', ':'))` via the `CanonicalSerializer`.
