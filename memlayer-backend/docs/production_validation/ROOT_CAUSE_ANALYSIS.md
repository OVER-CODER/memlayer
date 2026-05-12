# Phase D1.5 Production Validation — Root Cause Analysis

## 1. Overview
This document analyzes the failures and errors observed during the Phase D1.5 Production Validation of the MemLayer cognition substrate.

## 2. Failed Tests Analysis

### 2.1. `concurrent_ingestion`
- **Symptoms**: Memory creation failing under load (50 concurrent requests).
- **Root Causes**:
    - **Syntax Errors in Test**: The test script `test_concurrent_ingestion.py` contains invalid Python syntax (floating keyword arguments), likely causing execution to fail before any requests are made.
    - **Resource Starvation**: `AsyncSessionLocal` (and the sync counterpart) are configured with a `pool_size` of 5 and `max_overflow` of 5. A load of 50 concurrent requests causes connection pool exhaustion and timeouts.
    - **Sync/Async Mismatch**: API routes use synchronous `Session` while the production infrastructure is optimized for `AsyncSession`. Synchronous `db.commit()` calls in a threadpool lead to non-deterministic latency spikes under load.
- **Architectural Impact**: Risk of partial commits or race conditions if atomicity is not strictly enforced during pool exhaustion.

### 2.2. `pgvector_scaling`
- **Symptoms**: "No vector embedding data found" in retrieval tests.
- **Root Causes**:
    - **Missing Dependency**: `pgvector` is missing from `requirements.txt`.
    - **Fallback Activation**: `app/db/models.py` activates a `String` fallback for the `Vector` type when the library is missing.
    - **DB Incompatibility**: Production Neon DB uses the native `vector` type. Sending a JSON string from the application causes silent failures or type mismatches in the DB.
    - **Harness Errors**: Missing `get_auth_headers` import in `test_pgvector_scaling.py`.
- **Architectural Impact**: Loss of semantic retrieval capabilities; system degrades to keyword-only or fails entirely.

## 3. Error Tests Analysis (Auth/Header Issues)
Affected tests: `replay_integrity`, `governance_integrity`, `snapshot_recovery`, `partial_failure_recovery`, `async_ordering`, `high_volume_replay`.

- **Symptoms**: 401 Unauthorized or 422 Unprocessable Entity errors.
- **Root Causes**:
    - **Middleware Enforcement**: The production API now strictly enforces `AuthenticationMiddleware` and `TenantMiddleware`.
    - **Harness Deficiencies**: The production validation harness fails to correctly propagate the `Authorization` bearer token and `X-Tenant-ID` in all request paths.
    - **Trace ID Missing**: Some paths do not propagate the `X-Trace-Id` required for deterministic governance tracking.
- **Architectural Impact**: Inability to validate secure invariants (Lineage, Replay) in a protected environment.

## 4. Proposed Fixes

| Problem Area | Fix Strategy |
| :--- | :--- |
| **Auth Propagation**| Update `helpers.py` and all test scripts to use unified `get_auth_headers()`. Fix syntax errors. |
| **Concurrency** | Increase `pool_size` and `max_overflow` in `app/db/session.py`. |
| **PGVector** | Restore `pgvector` to `requirements.txt`. Ensure `Vector` type correctly binds to asyncpg. |
| **Harness Syntax** | Surgical fix of `httpx.post` calls in validation scripts. |

## 5. Conclusion
The observed failures are primarily due to **Harness Divergence** (test code falling behind architectural hardening) and **Dependency Regression** (`pgvector` removal). The core substrate logic remains stable but requires these surgical infrastructure fixes to achieve 100% validation.
