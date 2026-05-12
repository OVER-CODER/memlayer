# Failure Model Specification — v1

## 1. Overview
Defines how the MemLayer runtime responds to operational failures to ensure data integrity and fail-safe cognition.

## 2. Failure Taxonomy

### 2.1. Tolerated Failures (Graceful Recovery)
- **Transient Provider Error**: 429/503 from Anthropic/Gemini.
- **Action**: Exponential Backoff Retry (Max 3).
- **Result**: Success or escalated to Non-Tolerated.

- **Database Connection Dropout**: Temporary SQL stall.
- **Action**: Session retry via UoW.
- **Result**: Atomic recovery.

### 2.2. Non-Tolerated Failures (Immediate Halt)
- **Tenant Mismatch**: Detected by middleware.
- **Action**: Raise `403 Forbidden`, log high-severity audit event.
- **Result**: Request aborted.

- **Integrity Violation**: Checksum mismatch in lineage or replay.
- **Action**: Raise `RuntimeError`, halt workspace execution.
- **Result**: Prevent corrupted cognition.

## 3. Fail-Safe Behavior
- **Default State**: Protected. If a security or governance check fails, the runtime MUST default to "REJECT ACCESS."
- **Circuit Breaker**: 5 failures -> Provider CLOSED. No new requests sent for 60s.

## 4. Rollback Guarantees
- **Atomicity**: Any failure during a cognitive turn results in a full rollback of the `SQLUnitOfWork`.
- **Consistency**: The `semantic_lineage` remains at the last successful checkpoint. No "Half-Ingested" sessions allowed.

## 5. Split-Brain Prevention
- **Mechanism**: Distributed Locking in Redis.
- **Constraint**: Only ONE worker can hold the writer lock for a given `{tenant_id}:{workspace_id}`.
- **Result**: Deterministic ordering of historical events.

## 6. Critical Alerts
The following conditions trigger immediate operational intervention:
- `INTEGRITY_HASH_MISMATCH`
- `TENANT_ISOLATION_BREACH`
- `GOVERNANCE_PURGE_ATTEMPT`
- `REDIS_COORD_TIMEOUT_CONSECUTIVE`
