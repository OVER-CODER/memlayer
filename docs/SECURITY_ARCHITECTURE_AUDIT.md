# Security Architecture Audit — Phase C Hardening

## 1. Overview
This audit evaluates the current security posture of the MemLayer cognition runtime. It identifies trust boundaries, authentication gaps, and isolation weaknesses that must be addressed to transform the platform into secure enterprise infrastructure.

## 2. Identified Security Gaps

### 2.1. API Surface Gaps
- **Authentication**: Zero authentication currently implemented. All `/api/*` endpoints are publicly accessible.
- **Tenant Isolation**: While the database schema includes `tenant_id`, the current API routers and services do not enforce tenant filtering.
- **Input Validation**: Weak validation on large text payloads (potential for ReDoS or buffer exhaustion).

### 2.2. SDK & Auth Assumptions
- **Assumption**: SDKs are currently expected to provide a `tenant_id` but there is no server-side verification of this claim.
- **Risk**: Identity impersonation. A developer could access any workspace by simply providing the target `workspace_id`.

### 2.3. Coordination Layer (Redis)
- **Risk**: Redis keys are currently prefix-isolated by `workspace_id` but not explicitly authenticated per-tenant at the coordination level.
- **Bypass**: A malicious agent could potentially "sniff" or corrupt coordination locks of other tenants if they know the `workspace_id`.

### 2.4. Governance & Replay Gaps
- **Replay Access**: Historical traces can be retrieved by anyone with the `trace_id`.
- **Governance Visibility**: Audit trails contain sensitive runtime data (e.g., partial context) but are not protected by RBAC.

### 2.5. Persistence Isolation
- **Weakness**: Repositories rely on the caller to pass the correct `tenant_id`. There is no "Hard Isolation" middleware (like Postgres RLS) enforcing this at the engine level.

## 3. Trust Boundary Mapping

| Boundary | Current Status | Target (Phase C) |
| :--- | :--- | :--- |
| **User -> API** | Unauthenticated | **JWT / API Key** |
| **API -> Database**| Unfiltered | **Tenant-Scoped Session** |
| **Agent -> Redis** | Unauthenticated | **Lock Ownership Verification**|
| **Kernel -> S3** | Open Prefix | **Signed Path-Scoped Access** |

## 4. Operational Failure Risks
- **Backpressure**: No rate limiting on ingestion. High-frequency cognition runs could exhaust DB connection pools.
- **Secrets**: Provider API keys (Anthropic, Google) are currently loaded via env vars but not isolated/redacted in telemetry traces.

## 5. Audit Conclusions
MemLayer currently operates in a **"Zero-Trust Failure"** mode. The platform is operationally stable but architecturally insecure for multi-tenant enterprise use.

### Priority Fixes:
1.  Implement **JWT/API Key Authentication** for all API surfaces.
2.  Implement **Tenant Context Propagation** middleware.
3.  Implement **RBAC** for Replay and Governance access.
4.  Implement **Secret Redaction** in the telemetry stack.
